from __future__ import annotations

import threading
import time
import signal
import sys
from typing import Dict, List, Sequence

import pyautogui
 

from . import config
from . import snippets
from . import ui_actions
from . import waiters
import pyperclip
import json
import pandas as pd
import datetime
import os
from crm_search import _cleanup_callback
from . import hotkeys

# Variable globale pour stocker les résultats au fur et à mesure
_global_results: List[Dict] = []
_save_on_interrupt = True

def _save_partial_results():
    """Sauvegarde des résultats partiels en cas d'interruption"""

    global _global_results
    if _global_results and _save_on_interrupt:
        try:
            df = pd.DataFrame(_global_results)
            date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            base_name = config.OUTPUT_FILE.replace('.xlsx', f'_partial_{date_str}.xlsx')
            partial_file = base_name
            counter = 2
            while os.path.exists(partial_file):
                partial_file = base_name.replace('.xlsx', f'_{counter}.xlsx')
                counter += 1
            df.to_excel(partial_file, index=False)
            print(f"\n[SAUVEGARDE PARTIELLE] Résultats sauvegardés dans: {partial_file}")
            print(f"[SAUVEGARDE PARTIELLE] {len(_global_results)} résultats sauvegardés")
        except Exception as e:
            print(f"[ERREUR SAUVEGARDE PARTIELLE] {e}")

def _signal_handler(signum, frame):
    """Gestionnaire de signal pour les interruptions"""
    print(f"\n[INTERRUPTION DÉTECTÉE] Signal {signum} reçu")
    _save_partial_results()
    # Appeler le callback de nettoyage du module parent (clavier, etc.)
    if _cleanup_callback:
        _cleanup_callback()

    
    sys.exit(0)

def _clean_text(value: object) -> str:
    text = "" if value is None else str(value)
    return " ".join(text.split()).strip()


def _only_digits_plus(value: object) -> str:
    text = _clean_text(value)
    return "".join(ch for ch in text if ch.isdigit() or ch == "+")


def _normalize_contact(raw: Dict) -> Dict[str, str]:
    first_name = _clean_text(raw.get("firstName", ""))
    last_name = _clean_text(raw.get("lastName", ""))
    name = _clean_text(raw.get("name", "")).strip()
    fonction = _clean_text(raw.get("fonction", ""))
    if not name:
        name = f"{first_name} {last_name}".strip()

    email = _clean_text(raw.get("email", "")).lower()

    # Support both 'fix' and 'fixe' keys coming from the JS snippet
    fix_val = raw.get("fix", raw.get("fixe", ""))
    mobile = _only_digits_plus(raw.get("mobile", ""))
    fix = _only_digits_plus(fix_val)

    return {
        "name": name,
        "firstName": first_name,
        "lastName": last_name,
        "email": email,
        "mobile": mobile,
        "fix": fix,
        "fonction": fonction,
        
    }


def _run_interlocutor_search(stop_event: threading.Event, flag: Dict[str, bool]) -> None:
    try:
        idx, box = waiters.wait_for_any_image_on_screen(
            config.INTERLOCUTOR_BUTTON_IMAGES,
            timeout=20.0,
            interval=0.5,
            confidence=0.8,
            stop_event=stop_event,
        )
        if box:
            x, y, w, h = box
            center_x = x + w // 2
            center_y = y + h // 2
            variant_num = (idx + 1) if idx is not None else "?"
            print(f"   [OK] Bouton 'Interlocuteur' trouve (variante {variant_num}) a: {box}")
            pyautogui.click(center_x, center_y)
            time.sleep(0.8)
            print("   [OK] Bouton 'Interlocuteur' clique - Resultat trouve")
            flag["found"] = True
            stop_event.set()
            return
    except Exception as exc:
        print(f"   Erreur recherche 'Interlocuteur': {exc}")

def _run_pre_fetch_search(stop_event: threading.Event, flag: Dict[str, bool]) -> None:
    """
    Déclenche le clic sur le premier résultat via le snippet DOM, mais seulement
    après une période de grâce pendant laquelle on laisse une chance au bouton
    'Interlocuteur' d'apparaître naturellement. Ne s'appuie pas sur des images
    (peu fiables dans cet état transitoire) et ne considère pas le pré-fetch
    comme un état terminal (ne stoppe pas les autres threads).
    """
    try:
        start = time.time()
        grace_seconds = 13.0  # délai adaptable sans dépendre d'un pattern visuel fragile
        # Attente coopérative: sort si un autre thread a trouvé/terminé (stop_event)
        while not stop_event.is_set() and (time.time() - start) < grace_seconds:
            time.sleep(0.1)

        if not stop_event.is_set():
            print("   [..] Pré-fetch: déclenchement du clic 1er résultat (DOM)")
            snippets.run_dom_get_first_interlocuteurs_snippet()
            # Le snippet affiche un prompt avec le JSON des résultats.
            # Copie réalisée côté snippets._execute_snippet via Ctrl+A/C, on récupère ici.
            try:
                raw = pyperclip.paste()
                data = json.loads(raw) if raw else []
            except Exception:
                data = []
            flag["data"] = data
            flag["found"] = True
            # Si le pré-fetch a réellement retourné des données, on considère
            # cela comme un état terminal et on stoppe les autres threads.
            if data:
                stop_event.set()
            time.sleep(0.5)
    except Exception as exc:
        print(f"   Erreur recherche 'Pre-Fetch': {exc}")

def _run_no_result_search(stop_event: threading.Event, flag: Dict[str, bool]) -> None:
    try:
        box = waiters.wait_for_image_on_screen(
            config.NO_RESULT_IMAGE,
            timeout=20.0,
            interval=0.5,
            confidence=0.8,
            stop_event=stop_event,
        )
        if box:
            print(f"   [X] Message '0 resultat' detecte a: {box}")
            print("   [X] Aucun resultat trouve")
            flag["found"] = True
            stop_event.set()
            return
    except Exception as exc:
        print(f"   Erreur recherche message '0 resultat': {exc}")


def _process_single_phone(phone: str, is_last: bool, company_info_map: Dict = None) -> List[Dict]:
    results: List[Dict] = []
    
    # Récupérer les infos entreprise depuis le mapping (nom société + SIRET)
    company_info = {}
    if company_info_map and phone in company_info_map:
        company_info = company_info_map[phone]

    try:
        try:
            ui_actions.focus_search_field()
        except RuntimeError as exc:
            print(f"[X] ERREUR CRITIQUE: {exc}")
            print("[X] Le script s'arrete car le champ de recherche est introuvable")
            return []

        pyautogui.typewrite(str(phone), interval=0.05)
        time.sleep(0.5)
        ui_actions.submit_search()

        print("   Lancement de la recherche parallele...")

        interlocutor_found = {"found": False}
        no_result_found = {"found": False}
        pre_fetch_found = {"found": False}
        stop_event = threading.Event()

        thread_interlocutor = threading.Thread(
            target=_run_interlocutor_search,
            args=(stop_event, interlocutor_found),
            daemon=True,
        )
        thread_no_result = threading.Thread(
            target=_run_no_result_search,
            args=(stop_event, no_result_found),
            daemon=True,
        )
        thread_pre_fetch = threading.Thread(
            target=_run_pre_fetch_search,
            args=(stop_event, pre_fetch_found),
            daemon=True,
        )

        thread_interlocutor.start()
        thread_no_result.start()
        thread_pre_fetch.start()

        start_time = time.time()
        # Donne plus de marge pour: recherche -> éventuel pré-fetch -> chargement fiche -> bouton
        timeout = 30.0
        while time.time() - start_time < timeout:
            if interlocutor_found["found"]:
                print("   ✅ [OK] Resultat trouve via bouton 'Interlocuteur'")
                break
            if no_result_found["found"]:
                print("   [X] Aucun resultat - Message '0 resultat' detecte")
                time.sleep(0.5)
                break
            if pre_fetch_found["found"]:
                data = pre_fetch_found.get("data") or []
                if data:
                    print("   ✅ [OK] Pré-fetch: résultats du snippet confirmés, on continue")
                    time.sleep(1)
                    break
                else:
                    # Pré-fetch déclenché mais aucun résultat JSON confirmé
                    print("   [...] Pré-fetch détecté mais aucun résultat JSON encore confirmé…")
            time.sleep(0.1)

        stop_event.set()
        # Attendre la terminaison réelle des threads afin d'éviter
        # toute interférence avec le numéro suivant.
        thread_interlocutor.join()
        thread_no_result.join()
        thread_pre_fetch.join()

        # Succès si bouton trouvé OU si le pré-fetch a retourné des résultats JSON
        has_result = interlocutor_found["found"] or bool(pre_fetch_found.get("data"))

        if has_result:
        
            
            # On ouvre directement l'onglet Interlocuteur via snippet JS (sans dépendre d'images).
            print("   Ouverture de l'onglet Interlocuteur via snippet JS...")
            snippets.open_interlocuteur_tab()
            time.sleep(2)
            print("   Execution du snippet DOM Interlocuteur...")
            snippets.run_dom_interlocuteurs_snippet()
            # Récupérer le contenu du presse-papiers (clipboard)
            clipboard_content = pyperclip.paste()
            try:
                infos = json.loads(clipboard_content)
            except Exception as e:
                print(f"   Erreur lors de la lecture du presse-papiers: {e}")
                infos = []
            time.sleep(1)
            # OCR-based fallback supprimé (non utilisé)
        else:
            infos = []

        if not infos:
            status = "NOT_FOUND" if not has_result else "NO_CONTACT_FOUND"
            print(f"   Aucun contact pertinent pour {phone}")
            # On fixe explicitement toutes les colonnes attendues, même si vides
            results.append({
                "phone_searched": phone,
                "company": company_info.get('company', ''),
                "siret": company_info.get('siret', ''),
                "name": "",
                "mobile": "",
                "fix": "",
                "email": "",
                "fonction": "",
                "status": status,
            })
            time.sleep(0.5)
            if not has_result :
                ui_actions.open_console_and_close_window()
        else:
            print(f"   {len(infos)} contact(s) Direction/Dir. Generale pour {phone}")
            print(f"   Infos detaillees: {infos}")
            for info in infos:
                normalized = _normalize_contact(info if isinstance(info, dict) else {})
                results.append({
                    "phone_searched": phone,
                    "company": company_info.get('company', ''),
                    "siret": company_info.get('siret', ''),
                    "name": normalized.get("name", ""),
                    "mobile": normalized.get("mobile", ""),
                    "fix": normalized.get("fix", ""),
                    "email": normalized.get("email", ""),
                    "fonction": normalized.get("fonction", ""),
                    "category": info.get("category", ""),
                    "status": "FOUND",
                })

        if not is_last:
            print("Pause de 2 secondes... (vous pouvez reprendre le controle si necessaire)")
            time.sleep(2)

    except Exception as exc:
        print(f"   Erreur pour {phone}: {exc}")
        results.append({
            "phone_searched": phone,
            "company": company_info.get('company', ''),
            "siret": company_info.get('siret', ''),
            "name": "",
            "mobile": "",
            "fix": "",
            "email": "",
            "fonction": "",
            "status": f"Erreur: {exc}",
        })

    # Ajouter les résultats à la liste globale pour sauvegarde d'urgence
    global _global_results
    _global_results.extend(results)
    
    return results


def _process_single_phone_with_watcher(phone: str, is_last: bool, company_info_map: Dict = None) -> List[Dict]:
    """
    Version amelioree utilisant un watcher JS au lieu de 3 threads Python.
    Plus rapide, plus fiable, moins de CPU.
    """
    global _global_results  # Declarer au debut de la fonction
    results: List[Dict] = []
    
    # Recuperer les infos entreprise depuis le mapping
    company_info = {}
    if company_info_map and phone in company_info_map:
        company_info = company_info_map[phone]
    
    try:
        # 1. Focus et lancer la recherche
        try:
            ui_actions.focus_search_field()
        except RuntimeError as exc:
            print(f"[X] ERREUR CRITIQUE: {exc}")
            print("[X] Le script s'arrete car le champ de recherche est introuvable")
            return []
        
        pyautogui.typewrite(str(phone), interval=0.05)
        time.sleep(0.5)
        ui_actions.submit_search()
        
        # 2. Ouvrir la console et injecter le watcher JS
        print("   📡 Ouverture console et injection watcher JS...")
        hotkeys.open_chrome_console()
        time.sleep(0.8)
        
        # 3. Executer le watcher qui surveille les 3 conditions en parallele
        result = snippets.execute_watcher_snippet(
            'parallel_search_watcher.js',
            timeout=60.0
        )
        
        status = result.get('status')
        has_result = result.get('hasResult', False)
        elapsed_ms = result.get('elapsed', 0)
        
        print(f"   ⏱️  Detection en {elapsed_ms}ms: {status}")
        
        # 4. Traiter selon le statut detecte
        if status == 'NO_RESULT':
            print("   ❌ Aucun resultat trouve")
            results.append({
                "phone_searched": phone,
                "company": company_info.get('company', ''),
                "siret": company_info.get('siret', ''),
                "name": "",
                "mobile": "",
                "fix": "",
                "email": "",
                "fonction": "",
                "status": "NOT_FOUND",
            })
            time.sleep(0.5)
            if not is_last:
                ui_actions.open_console_and_close_window()
        
        elif status in ('INTERLOCUTEUR_FOUND', 'PREFETCH_READY'):
            print("   ✅ Resultat detecte, extraction des interlocuteurs...")
            
            # Si PREFETCH, c'est juste une etape de configuration pour preparer la page
            if status == 'PREFETCH_READY':
                print("   📊 Prefetch detecte - Configuration de la page...")
                snippets.run_dom_get_first_interlocuteurs_snippet()
                
                # Attendre le prompt avec les donnees
                time.sleep(1.5)            
                
                prefetch_data = pyperclip.paste().strip()
                
                # Fermer le prompt
                pyautogui.press('escape')
                time.sleep(0.3)
                
                # Verifier qu'il y a bien des donnees (JSON avec interlocuteurs)
                if not prefetch_data or prefetch_data == []:
                    print("   ⚠️  Prefetch vide - Aucun interlocuteur trouve")
                    results.append({
                        "phone_searched": phone,
                        "company": company_info.get('company', ''),
                        "siret": company_info.get('siret', ''),
                        "name": "",
                        "mobile": "",
                        "fix": "",
                        "email": "",
                        "fonction": "",
                        "status": "NO_CONTACT_FOUND",
                    })
                    if not is_last:
                        ui_actions.open_console_and_close_window()
                    _global_results.extend(results)
                    return results
                
                # Verifier que c'est du JSON valide
                try:
                    prefetch_json = json.loads(prefetch_data)
                    count = len(prefetch_json) if isinstance(prefetch_json, list) else 1
                    print(f"   ✅ Prefetch: {count} entreprise(s) trouvee(s), configuration OK")
                except json.JSONDecodeError:
                    print("   ⚠️  Prefetch: donnees invalides, on arrete")
                    results.append({
                        "phone_searched": phone,
                        "company": company_info.get('company', ''),
                        "siret": company_info.get('siret', ''),
                        "name": "",
                        "mobile": "",
                        "fix": "",
                        "email": "",
                        "fonction": "",
                        "status": "ERROR",
                    })
                    if not is_last:
                        ui_actions.open_console_and_close_window()
                    _global_results.extend(results)
                    return results
                
                time.sleep(2)  # Attendre que la page soit prete apres le clic
            
            # Ouvrir l'onglet Interlocuteur via snippet JS
            print("   Ouverture de l'onglet Interlocuteur via snippet JS...")
            snippets.open_interlocuteur_tab()
            time.sleep(2)
            
            print("   Execution du snippet DOM Interlocuteur...")
            snippets.run_dom_interlocuteurs_snippet()
            
            # Recuperer le contenu du presse-papiers
            clipboard_content = pyperclip.paste()
            try:
                infos = json.loads(clipboard_content)
            except Exception as e:
                print(f"   Erreur lors de la lecture du presse-papiers: {e}")
                infos = []
            
            time.sleep(1)
            
            if infos:
                print(f"   📊 {len(infos)} contact(s) trouves")
                for info in infos:
                    normalized = _normalize_contact(info if isinstance(info, dict) else {})
                    results.append({
                        "phone_searched": phone,
                        "company": company_info.get('company', ''),
                        "siret": company_info.get('siret', ''),
                        "name": normalized.get("name", ""),
                        "mobile": normalized.get("mobile", ""),
                        "fix": normalized.get("fix", ""),
                        "email": normalized.get("email", ""),
                        "fonction": normalized.get("fonction", ""),
                        "status": "FOUND",
                    })
            else:
                print("   ⚠️  Resultat trouve mais aucun contact extrait")
                results.append({
                    "phone_searched": phone,
                    "company": company_info.get('company', ''),
                    "siret": company_info.get('siret', ''),
                    "name": "",
                    "mobile": "",
                    "fix": "",
                    "email": "",
                    "fonction": "",
                    "status": "NO_CONTACT_FOUND",
                })
            
            if not is_last:
                print("Pause de 2 secondes...")
                time.sleep(2)
        
        else:  # TIMEOUT
            print("   ⏱️  Timeout - Aucune detection")
            results.append({
                "phone_searched": phone,
                "company": company_info.get('company', ''),
                "siret": company_info.get('siret', ''),
                "name": "",
                "mobile": "",
                "fix": "",
                "email": "",
                "fonction": "",
                "status": "TIMEOUT",
            })
            if not is_last:
                ui_actions.open_console_and_close_window()
    
    except Exception as exc:
        print(f"   Erreur pour {phone}: {exc}")
        results.append({
            "phone_searched": phone,
            "company": company_info.get('company', ''),
            "siret": company_info.get('siret', ''),
            "name": "",
            "mobile": "",
            "fix": "",
            "email": "",
            "fonction": "",
            "status": f"Erreur: {exc}",
        })
    
    # Ajouter les resultats a la liste globale pour sauvegarde d'urgence
    _global_results.extend(results)
    
    return results


def process_phone_numbers(phone_numbers: Sequence[str], company_info_map: Dict = None) -> List[Dict]:
    # Configurer le gestionnaire de signal pour les interruptions
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)
    
    # Réinitialiser la liste globale des résultats
    global _global_results
    _global_results.clear()
    
    aggregated: List[Dict] = []
    for index, phone in enumerate(phone_numbers):
        print(f"\nRecherche {index + 1}/{len(phone_numbers)}: {phone}")
        aggregated.extend(_process_single_phone_with_watcher(phone, is_last=index == len(phone_numbers) - 1, company_info_map=company_info_map))
    return aggregated


__all__ = ["process_phone_numbers"]



