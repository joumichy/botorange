#!/usr/bin/env python3
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
    hash_value = os.environ.get("CRM_LICENSE_HASH")
    if hash_value:
        return hash_value.strip()
    
    print("[INFO] Configurez CRM_LICENSE_HASH dans config.py")
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
            # Windows: %LOCALAPPDATA%\.crm\
            base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        else:
            # Mac/Linux: ~/.crm/
            base = os.path.expanduser("~")
        base = os.path.join(base, ".crm")
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
    # Always returns the same, fixed value (for testing or override)
    return "FIXED-MACHINE-ID-123456789ABCDEF"


def _load_or_init_cfg() -> dict:
    cfg_path = _cfg_path()
    if os.path.isfile(cfg_path):
        try:
            return json.load(open(cfg_path, "r", encoding="utf-8"))
        except Exception:
            pass
    cfg = {"status": "oopa", "key": hashlib.sha256(b"crm-default-key").hexdigest()}
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
    except Exception as e:
        print(f"[ERREUR] Impossible de sauvegarder le fichier de trial: {e}")
        print(f"[ERREUR] Chemins: {p1}, {p2}")
        # Le répertoire devrait déjà exister grâce à _get_secure_base_dir()
        base_dir = _get_secure_base_dir()
        print(f"[INFO] Répertoire de base: {base_dir}")
        print(f"[INFO] Existe: {os.path.exists(base_dir)}")


def _validate_trial(cfg: dict, t: dict | None, tb: dict | None) -> tuple[int, int] | None:
    if cfg.get("status") != "oopa" or not cfg.get("key"):
        print("[ERREUR] trial_config.json invalide ou manquant")
        return None
    if not t or not tb:
        return None
    key = str(cfg.get("key"))
    if t != tb:
        raise SystemExit("Fichiers trial incohérents")
    for obj in (t, tb):
        try:
            first = int(obj.get("first_run", 0))
            last = int(obj.get("last_run", 0))
            mid = str(obj.get("mid", ""))
            sig = str(obj.get("sig", ""))
            obj_key = str(obj.get("key", ""))
            if mid != _machine_id():
                raise SystemExit("ID machine modifié")
            if sig != _sign_trial(first, last, key, mid):
                raise SystemExit("Signature invalide")
            if obj_key != key:
                raise SystemExit("Clé invalide")
            now = int(time.time())
            if last > now + 3600:
                raise SystemExit("Horloge future détectée")
        except SystemExit:
            raise
        except Exception as e:
            raise SystemExit(f"Trial corrompu: {e}")
    return int(t.get("first_run", 0)), int(t.get("last_run", 0))


def _unlock_prompt(expected_hash: str) -> bool:
    try:
        pw = getpass("Entrez le mot de passe pour déverrouiller: ")
    except Exception:
        pw = input("Entrez le mot de passe pour déverrouiller: ")
    if _hash_pw(pw) == expected_hash:
        _write_unlock(expected_hash)
        print("Déverrouillé avec succès.")
        return True
    print("Mot de passe invalide. Fermeture.")
    return False


def ensure_trial(expected_hash: str | None) -> bool:
    """Enforce 14-day trial and allow unlock via password.

    Returns True if allowed to run; False otherwise.
    """
    if expected_hash and _is_unlocked(expected_hash):
        return True

    cfg = _load_or_init_cfg()
    key = str(cfg.get("key", ""))
    mid = _machine_id()
    now = int(time.time())
    window = 14 * 24 * 3600

    t, tb = _read_trial_pair()
    try:
        valid = _validate_trial(cfg, t, tb)
        if not valid:
            print("[INFO] ⏳ Initialisation des fichiers d'essai...")
            _write_trial_pair(now, now, key, mid)
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

    if now - first <= window:
        remaining = window - (now - first)
        days = remaining // 86400
        hours = (remaining % 86400) // 3600
        minutes = (remaining % 3600) // 60
        print(f"[Période d'essai] ⏳ Temps restant : {days}j {hours}h {minutes}min")
        return True

    print("\n[Essai expiré] Cette version est limitée.")
    if not expected_hash:
        print("Définissez CRM_LICENSE_HASH dans .env pour déverrouiller.")
        return False
    return _unlock_prompt(expected_hash)

