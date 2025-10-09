#!/usr/bin/env python3
"""
Lanceur principal Kompass (point d'entrée recommandé)

- Charge la configuration (.env) à côté du binaire/script
- Résout le chemin des navigateurs Playwright en mode dev/installed
- Applique la politique d'essai/déverrouillage via security_utils
- Appelle main.main() (async) pour démarrer l'app
"""
from __future__ import annotations
from config import KOMPASS_LICENSE_HASH

import asyncio
import os
import sys

from security_utils import load_expected_hash, ensure_trial


try:
    from main import main as app_main  # inclusion de main.py lors du freeze
except Exception:
    app_main = None  # type: ignore[assignment]


def _get_script_dir() -> str:
    """Retourne le dossier du script (dev) ou de l'exécutable (installé)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _set_bundled_playwright_browsers() -> None:
    """Résout PLAYWRIGHT_BROWSERS_PATH pour dev et .app/.exe."""
    candidates: list[str] = []
    script_dir = _get_script_dir()
    candidates.append(os.path.join(script_dir, "playwright-browsers"))

    # macOS .app parent traversal
    parent = script_dir
    for _ in range(4):
        parent = os.path.dirname(parent)
        if not parent:
            break
        candidates.append(os.path.join(parent, "playwright-browsers"))

    # PyInstaller temp and CWD fallbacks
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(os.path.join(meipass, "playwright-browsers"))
        candidates.append(os.path.join(os.path.dirname(meipass), "playwright-browsers"))
    candidates.append(os.path.join(os.getcwd(), "playwright-browsers"))

    for c in candidates:
        if os.path.isdir(c):
            os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", c)
            break


def _load_env_file() -> None:
    """Injecte le hash de licence depuis config.py (plus de .env utilisé)."""
    try:
        os.environ.setdefault("KOMPASS_LICENSE_HASH", KOMPASS_LICENSE_HASH)
    except Exception:
        pass


def main() -> None:
    _set_bundled_playwright_browsers()
    _load_env_file()

    # Trial / unlock
    expected_hash = load_expected_hash()
    if not ensure_trial(expected_hash):
        sys.exit(2)

    print("=== Scraper Kompass EasyBusiness ===")
    print("Ce lanceur démarre le script principal.")
    print()

    try:
        global app_main
        if app_main is None:
            from main import main as app_main  # type: ignore[no-redef]
        asyncio.run(app_main())  # type: ignore[misc]
    except KeyboardInterrupt:
        print("\nInterrompu par l'utilisateur")
    except Exception as e:
        print(f"Erreur inattendue: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

