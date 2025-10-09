#!/usr/bin/env python3
"""
Lanceur principal (exécutable) pour la recherche CRM.

Charge config.py, applique la politique d'essai/déverrouillage (CRM_LICENSE_HASH)
via security_utils, puis appelle crm_search.main().
"""
from __future__ import annotations

import os
import sys
import locale
import platform
import subprocess
import ctypes
import time

from security_utils import load_expected_hash, ensure_trial
from modules.config import CRM_LICENSE_HASH
from crm_search import main as app_main
from crm_search import set_cleanup_callback


def _load_config() -> None:
    """Injecte le hash de licence depuis config.py (plus de .env utilisé)."""
    try:
        os.environ.setdefault("CRM_LICENSE_HASH", CRM_LICENSE_HASH)
    except Exception:
        pass

def set_keyboard_english():
    """Bascule le clavier en anglais (US), selon le système."""
    system = platform.system()

    if system == "Windows":
         # --- Windows : exécuter la commande PowerShell ---
            LANG_EN = 0x0409  # English (US)
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            # Active le layout anglais (US)
            ctypes.windll.user32.ActivateKeyboardLayout(ctypes.c_ulong(LANG_EN), 0)
            ctypes.windll.user32.PostMessageW(hwnd, 0x0050, LANG_EN, 0)
            print("[INFO] ✅ Clavier basculé en anglais (US) [Windows]")
            
    elif system == "Darwin":  # macOS
        script = '''
        tell application "System Events"
            tell process "SystemUIServer"
                set menuExtras to every menu bar item of menu bar 1
                repeat with m in menuExtras
                    if description of m contains "text input" or description of m contains "input" then
                        click m
                        delay 0.1
                        click menu item "U.S." of menu 1 of m
                        exit repeat
                    end if
                end repeat
            end tell
        end tell
        '''
        subprocess.run(["osascript", "-e", script])
        print("[INFO] Clavier basculé en anglais (U.S.) sur macOS")
    else:
        print("[WARN] OS non supporté pour le changement de clavier en anglais.")

    time.sleep(0.2)


def set_keyboard_french():
    """Bascule le clavier en français (FR), selon le système."""
    system = platform.system()

    if system == "Windows":
        # --- Windows : exécuter la commande PowerShell ---
            cmd = [
                "powershell",
                "-Command",
                "Set-WinUserLanguageList fr-FR -Force"
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("[INFO] ✅ Clavier basculé en français (FR) via PowerShell")
           

    elif system == "Darwin":  # macOS
        script = '''
        tell application "System Events"
            tell process "SystemUIServer"
                set menuExtras to every menu bar item of menu bar 1
                repeat with m in menuExtras
                    if description of m contains "text input" or description of m contains "input" then
                        click m
                        delay 0.1
                        click menu item "Français" of menu 1 of m
                        exit repeat
                    end if
                end repeat
            end tell
        end tell
        '''
        subprocess.run(["osascript", "-e", script])
        print("[INFO] Clavier basculé en français sur macOS")
    else:
        print("[WARN] OS non supporté pour le changement de clavier en français.")

    time.sleep(0.2)


def main() -> None:
    print("=== Recherche CRM Orange ===")
    print("Ce lanceur va démarrer la recherche dans le CRM à partir d'un Excel Kompass.")
    print()

    _load_config()
    set_keyboard_english()

    # Enregistrer le callback de nettoyage (clavier français)
    set_cleanup_callback(set_keyboard_french)

    expected_hash = load_expected_hash()
    if not ensure_trial(expected_hash):
        set_keyboard_french()  # Remettre en français même si échec licence
        sys.exit(2)

    try:
        app_main()
    except KeyboardInterrupt:
        print("\nScript interrompu par l'utilisateur")
    except Exception as e:
        print(f"Erreur inattendue: {e}")
        raise
    finally:
        # Toujours remettre le clavier en français, quelle que soit la sortie
        print("\n[CLEANUP] Remise du clavier en français...")
        set_keyboard_french()


if __name__ == "__main__":
    main()

