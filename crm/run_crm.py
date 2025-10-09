#!/usr/bin/env python3
"""
Lanceur principal (exécutable) pour la recherche CRM.

Charge config.py, applique la politique d'essai/déverrouillage (CRM_LICENSE_HASH)
via security_utils, puis appelle crm_search.main().
"""
from __future__ import annotations

import os
import sys
from security_utils import load_expected_hash, ensure_trial
from modules.config import CRM_LICENSE_HASH


def _get_script_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _load_config() -> None:
    """Injecte le hash de licence depuis config.py (plus de .env utilisé)."""
    try:
        os.environ.setdefault("CRM_LICENSE_HASH", CRM_LICENSE_HASH)
    except Exception:
        pass


def main() -> None:
    from crm_search import main as app_main

    print("=== Recherche CRM Orange ===")
    print("Ce lanceur va démarrer la recherche dans le CRM à partir d'un Excel Kompass.")
    print()

    _load_config()

    expected_hash = load_expected_hash()
    if not ensure_trial(expected_hash):
        sys.exit(2)

    try:
        app_main()
    except KeyboardInterrupt:
        print("\nScript interrompu par l'utilisateur")
    except Exception as e:
        print(f"Erreur inattendue: {e}")


if __name__ == "__main__":
    main()

