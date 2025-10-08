#!/usr/bin/env python3
"""
Lanceur principal (exécutable) pour la recherche CRM.

Appelle directement crm_search.main() pour compatibilité PyInstaller.
"""
from __future__ import annotations


def main() -> None:
    from crm_search import main as app_main

    print("=== Recherche CRM Orange ===")
    print("Ce lanceur va démarrer la recherche dans le CRM à partir d'un Excel Kompass.")
    print()

    try:
        app_main()
    except KeyboardInterrupt:
        print("\nScript interrompu par l'utilisateur")
    except Exception as e:
        print(f"Erreur inattendue: {e}")


if __name__ == "__main__":
    main()

