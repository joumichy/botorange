#!/usr/bin/env python3
"""
Script pour rechercher les numeros de telephone dans le CRM Orange.
Le code est desormais organise dans le dossier modules/ pour plus de clarte.
"""

from __future__ import annotations

import time
import signal
import sys
from typing import Iterable, List
import datetime
import pandas as pd
import os
import glob
import subprocess

# Tkinter (optionnel). Fallback AppleScript/console si absent (ex: macOS sans Tk)
try:
    import tkinter as tk
    from tkinter import filedialog
    HAS_TK = True
except Exception:
    HAS_TK = False

from modules import config, filesystem, snippets, ui_actions, workflow

# Variable pour stocker les résultats partiels
_partial_results: list[dict] = []


def _save_partial_results():
    """Sauvegarde les résultats partiels en cas d'interruption"""
    global _partial_results
    if _partial_results:
        try:
            df = pd.DataFrame(_partial_results)
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")
            partial_file = config.OUTPUT_FILE.replace('.xlsx', f'_partial_{date_str}.xlsx')
            df.to_excel(partial_file, index=False)
            print(f"\n[SAUVEGARDE PARTIELLE] Résultats sauvegardés dans: {partial_file}")
            print(f"[SAUVEGARDE PARTIELLE] {len(_partial_results)} résultats sauvegardés")
        except Exception as e:
            print(f"[ERREUR SAUVEGARDE PARTIELLE] {e}")


def _signal_handler(signum, frame):
    """Gestionnaire de signal pour les interruptions dans crm_search.py"""
    print(f"\n[INTERRUPTION DÉTECTÉE] Signal {signum} reçu dans crm_search.py")
    _save_partial_results()
    sys.exit(0)


def _clean_phone_numbers(raw_numbers: Iterable[object]) -> List[str]:
    cleaned: List[str] = []
    for value in raw_numbers:
        phone_str = str(value).strip()
        if not phone_str:
            continue
        normalized = (
            phone_str.replace('+33', '')
            .replace(' ', '')
            .replace('-', '')
            .replace('.', '')
        )
        digits = ''.join(ch for ch in normalized if ch.isdigit())
        if digits and len(digits) >= 9:
            if not digits.startswith('0'):
                digits = '0' + digits
            cleaned.append(digits)
    return cleaned


def _ask_file_osascript_excel() -> str:
    """macOS file picker (osascript) limité aux fichiers Excel."""
    if sys.platform != "darwin":
        return ""
    script = (
        'set excelTypes to {"org.openxmlformats.spreadsheetml.sheet","com.microsoft.excel.xls"}\n'
        'try\n'
        '    set f to choose file with prompt "Sélectionne un fichier Excel" of type excelTypes\n'
        '    POSIX path of f\n'
        'on error\n'
        '    ""\n'
        'end try'
    )
    try:
        res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        return (res.stdout or "").strip()
    except Exception:
        return ""


def _select_excel_file() -> str:
    """Sélectionne un fichier Excel (Tkinter → AppleScript macOS → console)."""
    if HAS_TK:
        try:
            root = tk.Tk()
            root.withdraw()
            path = filedialog.askopenfilename(
                title="Sélectionner le fichier Kompass Excel",
                filetypes=[("Fichiers Excel", "*.xlsx *.xls")],
                initialdir=str(config.BASE_DIR),
            )
            root.destroy()
            if path:
                return path
        except Exception:
            pass
    path = _ask_file_osascript_excel()
    if path:
        return path
    print("Tkinter/AppleScript indisponible. Saisie en console.")
    candidates = []
    for d in [os.getcwd(), str(config.BASE_DIR)]:
        candidates.extend(glob.glob(os.path.join(d, "*.xlsx")))
        candidates.extend(glob.glob(os.path.join(d, "*.xls")))
    if candidates:
        print("Fichiers détectés:")
        for idx, p in enumerate(candidates, 1):
            print(f"  {idx}. {p}")
        choice = input("Choisissez un fichier (numéro) ou laissez vide pour 1: ").strip()
        try:
            return candidates[(int(choice) - 1) if choice else 0]
        except Exception:
            return candidates[0]
    return input("Chemin du fichier Excel (.xlsx/.xls): ").strip()


def main() -> None:
    print("=== Recherche CRM Orange ===")
    print("Astuce: Appuyez sur Ctrl+C à tout moment pour sauvegarder les résultats partiels")

    # Configurer le gestionnaire de signal pour les interruptions
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # Réinitialiser les résultats partiels
    global _partial_results
    _partial_results.clear()

    # Sélection du fichier Kompass
    input_file = _select_excel_file()

    if not input_file:
        print("Aucun fichier sélectionné. Arrêt du programme.")
        return

    # Vérifier que le fichier est bien un fichier Excel
    if not input_file.lower().endswith(('.xlsx', '.xls')):
        print("Erreur: Seuls les fichiers Excel (.xlsx, .xls) sont acceptés.")
        print(f"Fichier sélectionné: {input_file}")
        return

    print(f"Fichier sélectionné: {input_file}")

    try:
        df = pd.read_excel(input_file, sheet_name='Entreprises')
        print(f"{len(df)} entreprises trouvées dans le fichier Excel")
    except Exception as exc:
        print(f"Erreur lors de la lecture du fichier Excel: {exc}")
        print("Vérifiez que le fichier contient une feuille nommée 'Entreprises'")
        return

    if 'phone' not in df.columns:
        print("Colonne 'phone' non trouvée dans le fichier")
        return

    phone_numbers = _clean_phone_numbers(df['phone'].dropna().tolist())
    if not phone_numbers:
        print("Aucun numero de telephone trouve")
        return

    print(f"{len(phone_numbers)} numeros de telephone a rechercher")

    print("\n=== INSTRUCTIONS ===")
    print("1. Ouvrez votre VM dans le navigateur")
    print("2. Naviguez jusqu'au champ de recherche")
    print("3. Revenez dans la console et appuyez sur Entree")
    print("4. Le script va automatiquement prendre le controle")
    print()
    print("\nAstuce (DOM Interlocuteur):")
    print(" - Lancer d'abord le script d'ouverture (console) puis, dans le nouvel onglet, executer le script d'extraction.")

    input("Appuyez sur Entree quand vous etes pret (VM ouverte avec champ de recherche visible)...")

    print("Demarrage du script dans 3 secondes...")
    time.sleep(3)

    ui_actions.calibrate_search_region()

    try:
        results = workflow.process_phone_numbers(phone_numbers)

        # Stocker les résultats partiels pour sauvegarde d'urgence
        _partial_results.extend(results)

        if not results:
            print("\n[X] Aucun resultat - le script s'est arrete prematurely")
            return

        try:
            pd.DataFrame(results).to_excel(config.OUTPUT_FILE, index=False)
            print(f"\nTermine. Resultats sauvegardes dans {config.OUTPUT_FILE}")
        except Exception as exc:
            print(f"Erreur lors de la sauvegarde des resultats: {exc}")

    except KeyboardInterrupt:
        print("\n[INTERRUPTION] Sauvegarde des résultats partiels...")
        _save_partial_results()
        return
    except Exception as exc:
        print(f"\n[ERREUR] {exc}")
        _save_partial_results()
        return


if __name__ == "__main__":
    main()

