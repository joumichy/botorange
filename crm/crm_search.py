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
import tkinter as tk
from tkinter import filedialog, messagebox

from modules import config, filesystem, snippets, ui_actions, workflow

# Variable pour stocker les résultats partiels
_partial_results = []

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


def main() -> None:
    print("=== Recherche CRM Orange ===")
    print("💡 Astuce: Appuyez sur Ctrl+C à tout moment pour sauvegarder les résultats partiels")
    
    # Configurer le gestionnaire de signal pour les interruptions
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)
    
    # Réinitialiser les résultats partiels
    global _partial_results
    _partial_results.clear()

    # Sélection du fichier Kompass via interface graphique
    print("Ouverture de la fenêtre de sélection de fichier...")
    
    # Créer une fenêtre Tkinter cachée
    root = tk.Tk()
    root.withdraw()  # Cacher la fenêtre principale
    
    # Ouvrir le dialogue de sélection de fichier
    input_file = filedialog.askopenfilename(
        title="Sélectionner le fichier Kompass Excel",
        filetypes=[
            ("Fichiers Excel", "*.xlsx *.xls")
        ],
        initialdir="."  # Dossier courant
    )
    
    # Fermer la fenêtre Tkinter
    root.destroy()
    
    if not input_file:
        print("Aucun fichier sélectionné. Arrêt du programme.")
        return
    
    # Vérifier que le fichier est bien un fichier Excel
    if not input_file.lower().endswith(('.xlsx', '.xls')):
        print("❌ Erreur: Seuls les fichiers Excel (.xlsx, .xls) sont acceptés.")
        print(f"Fichier sélectionné: {input_file}")
        return
    
    print(f"Fichier sélectionné: {input_file}")

    try:
        df = pd.read_excel(input_file, sheet_name='Entreprises')
        print(f"✅ {len(df)} entreprises trouvées dans le fichier Excel")
    except Exception as exc:
        print(f"❌ Erreur lors de la lecture du fichier Excel: {exc}")
        print("Vérifiez que le fichier contient une feuille nommée 'Entreprises'")
        return

    if 'phone' not in df.columns:
        print("Colonne 'phone' non trouvee dans le fichier")
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
