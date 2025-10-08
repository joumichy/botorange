#!/usr/bin/env python3
"""
Lanceur principal du scraper Kompass (point d'entrée recommandé)

Exécute directement la fonction `main()` du module `main` pour être
compatible avec un exécutable PyInstaller (frozen) et l'exécution source.
"""
from __future__ import annotations

import os
import sys
import asyncio

try:
    from main import main as app_main  # assure l'inclusion de main.py lors du freeze
except Exception:
    app_main = None  # type: ignore[assignment]


def _set_bundled_playwright_browsers() -> None:
    """Privilégie un dossier local `playwright-browsers` si présent."""
    candidates = []
    base_dir = os.path.dirname(getattr(sys, "executable", "") or os.path.abspath(__file__))
    candidates.append(os.path.join(base_dir, "playwright-browsers"))

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(os.path.join(meipass, "playwright-browsers"))
        candidates.append(os.path.join(os.path.dirname(meipass), "playwright-browsers"))

    candidates.append(os.path.join(os.getcwd(), "playwright-browsers"))

    for c in candidates:
        if os.path.isdir(c):
            os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", c)
            break


def main() -> None:
    _set_bundled_playwright_browsers()

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

