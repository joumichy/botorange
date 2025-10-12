#!/usr/bin/env python3
"""
Fonctions de sécurité et de gestion de licence/essai pour Kompass.

- Lecture du hash de licence (via .env à côté du binaire/script)
- Gestion de l'essai (paire .trial.json/.trial.bak.json signées)
- Déverrouillage par mot de passe (license.key)

Toutes les opérations de lecture/écriture se font relativement à `script_dir`,
ce qui rend le module utilisable en mode développement et en mode installé.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import uuid
from getpass import getpass


def _hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()


def load_expected_hash() -> str | None:
    """Retourne le hash de licence attendu depuis les variables d'environnement"""
    hash_value = os.environ.get("KOMPASS_LICENSE_HASH")
    if hash_value:
        return hash_value.strip()
    print("[INFO] Configurez KOMPASS_LICENSE_HASH")
    return None


def _is_unlocked(expected_hash: str | None) -> bool:
    base = _get_secure_base_dir()
    path = os.path.join(base, "license.key")
    try:
        if os.path.isfile(path):
            data = open(path, "r", encoding="utf-8").read().strip()
            return expected_hash is not None and data == expected_hash
    except Exception:
        return False
    return False


def _write_unlock(expected_hash: str) -> None:
    try:
        base = _get_secure_base_dir()
        path = os.path.join(base, "license.key")
        with open(path, "w", encoding="utf-8") as f:
            f.write(expected_hash)
        print(f"[INFO] Licence déverrouillée: {path}")
    except Exception as e:
        print(f"[ERREUR] Impossible de sauvegarder la licence: {e}")


def _get_secure_base_dir() -> str:
    """Retourne le répertoire de base sécurisé selon le mode d'exécution"""
    if getattr(sys, 'frozen', False):
        # Mode exécutable - utiliser le répertoire utilisateur caché
        if sys.platform == "win32":
            # Windows: %LOCALAPPDATA%\.kompass\
            base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        else:
            # Mac/Linux: ~/.kompass/
            base = os.path.expanduser("~")
        base = os.path.join(base, ".kompass")
    else:
        # Mode développement - utiliser le dossier du script
        base = os.path.dirname(__file__)
    
    os.makedirs(base, exist_ok=True)
    return base


def _cfg_path() -> str:
    """Retourne le chemin du fichier de configuration"""
    base = _get_secure_base_dir()
    return os.path.join(base, "trial_config.json")


def _trial_paths() -> tuple[str, str]:
    """Retourne les chemins des fichiers trial"""
    base = _get_secure_base_dir()
    return (
        os.path.join(base, "trial.json"),
        os.path.join(base, "trial.bak.json"),
    )


def _machine_id() -> str:
    try:
        nid = uuid.getnode()
    except Exception:
        nid = 0
    return hashlib.sha256(str(nid).encode("utf-8")).hexdigest()


def _load_or_init_cfg() -> dict:
    cfg_path = _cfg_path()
    if os.path.isfile(cfg_path):
        try:
            return json.load(open(cfg_path, "r", encoding="utf-8"))
        except Exception:
            pass
    # Status attendu et clé "en dur" (cohérente avec le code existant)
    cfg = {"status": "oopa", "key": hashlib.sha256(b"kompass-default-key").hexdigest()}
    try:
        json.dump(cfg, open(cfg_path, "w", encoding="utf-8"))
    except Exception:
        pass
    return cfg


def _sign_trial(first: int, last: int, key: str, mid: str) -> str:
    data = f"{first}:{last}:{mid}:{key}".encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _read_trial_pair() -> tuple[dict | None, dict | None]:
    p1, p2 = _trial_paths()
    t1 = t2 = None
    try:
        if os.path.isfile(p1):
            t1 = json.load(open(p1, "r", encoding="utf-8"))
    except Exception:
        t1 = None
    try:
        if os.path.isfile(p2):
            t2 = json.load(open(p2, "r", encoding="utf-8"))
    except Exception:
        t2 = None
    return t1, t2


def _write_trial_pair(first: int, last: int, key: str, mid: str) -> None:
    sig = _sign_trial(first, last, key, mid)
    obj = {"first_run": first, "last_run": last, "mid": mid, "sig": sig, "key": key}
    p1, p2 = _trial_paths()
    
    # Le répertoire est déjà créé par _get_secure_base_dir()
    try:
        with open(p1, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2)
        with open(p2, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2)
        print(f"[INFO] Fichiers de configuration établis.")
    except Exception as e:
        print(f"[ERREUR] Impossible de sauvegarder le fichier de trial: {e}")
        print(f"[ERREUR] Chemins: {p1}, {p2}")
        # Le répertoire devrait déjà exister grâce à _get_secure_base_dir()
        base_dir = _get_secure_base_dir()
        print(f"[INFO] Répertoire de base: {base_dir}")
        print(f"[INFO] Existe: {os.path.exists(base_dir)}")


def _validate_trial(cfg: dict, t: dict | None, tb: dict | None) -> tuple[int, int] | None:
    """Valide la cohérence entre config et paires trial (tamper checks)."""
    if cfg.get("status") != "oopa" or not cfg.get("key"):
        print("[ERREUR] trial_config.json invalide ou manquant")
        return None
    if not t or not tb:
        return None
    key = str(cfg.get("key"))
    if t != tb:
        print("[ERREUR CRITIQUE] Fichiers trial incohérents: .trial.json != .trial.bak.json")
        raise SystemExit("Tentative de modification des fichiers trial détectée")
    for obj_name, obj in [(".trial.json", t), (".trial.bak.json", tb)]:
        try:
            first = int(obj.get("first_run", 0))
            last = int(obj.get("last_run", 0))
            mid = str(obj.get("mid", ""))
            sig = str(obj.get("sig", ""))
            obj_key = str(obj.get("key", ""))

            expected_mid = _machine_id()
            if mid != expected_mid:
                raise SystemExit(f"ID machine modifié dans {obj_name}")
            expected_sig = _sign_trial(first, last, key, mid)
            if sig != expected_sig:
                raise SystemExit(f"Signature modifiée dans {obj_name}")
            if obj_key != key:
                raise SystemExit(f"Clé invalide dans {obj_name}")

            now = int(time.time())
            if last > now + 3600:  # 1h de marge
                raise SystemExit(f"Horloge future détectée dans {obj_name}")
        except SystemExit:
            raise
        except Exception as e:
            print(f"[ERREUR CRITIQUE] Validation {obj_name} impossible: {e}")
            raise SystemExit(f"Fichier {obj_name} corrompu ou modifié")
    return int(t.get("first_run", 0)), int(t.get("last_run", 0))


def _unlock_prompt(expected_hash: str) -> bool:
    try:
        pw = getpass("Entrez le mot de passe pour déverrouiller: ")
    except Exception:
        pw = input("Entrez le mot de passe pour déverrouiller: ")
    if _hash_pw(pw) == expected_hash:
        _write_unlock(expected_hash)
        os.environ.pop("KOMPASS_MAX_ROWS", None)
        print("Déverrouillé avec succès.")
        return True
    print("Mot de passe invalide. Fermeture.")
    return False


def ensure_trial(expected_hash: str | None) -> bool:
    """Fait respecter l'essai avec intégrité et effectue le déverrouillage.

    Retourne True si l'exécution est autorisée; False sinon.
    Définit KOMPASS_MAX_ROWS=20 pendant l'essai.
    """
    if expected_hash and _is_unlocked(expected_hash):
        return True

    cfg = _load_or_init_cfg()
    key = str(cfg.get("key", ""))
    mid = _machine_id()
    now = int(time.time())
    days14 = 14 * 24 * 3600  # 14 jours (conservé tel quel du code courant)

    t, tb = _read_trial_pair()
    try:
        valid = _validate_trial(cfg, t, tb)
        if not valid:
            # Premier lancement ou fichiers absents → initialiser
            print("[INFO] ⏳ Initialisation des fichiers d'essai...")
            _write_trial_pair(now, now, key, mid)
            os.environ["KOMPASS_MAX_ROWS"] = "300"
            return True
    except SystemExit as e:
        print(f"[ERREUR CRITIQUE] {e}")
        sys.exit(1)

    first, last = valid
    if now + 3600 < last:
        print("[INFO] Horloge système incohérente. Mot de passe requis.")
        if expected_hash and _unlock_prompt(expected_hash):
            return True
        return False

    if now > last:
        _write_trial_pair(first, now, key, mid)

    if now - first <= days14:
        remaining = days14 - (now - first)
        days = remaining // 86400
        hours = (remaining % 86400) // 3600
        minutes = (remaining % 3600) // 60
        print(f"[Période d'essai] ⏳ Temps restant : {days}j {hours}h {minutes}min")
        os.environ["KOMPASS_MAX_ROWS"] = "300"
        return True

    print("\n[Essai expiré] Cette version est limitée.")
    if not expected_hash:
        print("Aucun mot de passe attendu n'est configuré. Définissez KOMPASS_LICENSE_HASH dans .env.")
        return False
    return _unlock_prompt(expected_hash)

