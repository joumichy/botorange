#!/usr/bin/env python3
"""
Script de lancement pour la recherche CRM
"""
import subprocess
import sys

def main():
    """Lancer le script de recherche CRM"""
    print("=== Recherche CRM Orange ===")
    print("Ce script va utiliser les numéros du fichier Excel Kompass")
    print("et les rechercher dans le CRM Orange")
    print()
    
    try:
        # Lancer le script principal
        subprocess.run([sys.executable, "crm_search.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'exécution: {e}")
    except KeyboardInterrupt:
        print("\nScript interrompu par l'utilisateur")
    except Exception as e:
        print(f"Erreur inattendue: {e}")

if __name__ == "__main__":
    main()
