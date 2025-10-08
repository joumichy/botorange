from __future__ import annotations

import os
import time
from typing import Sequence

import pyautogui
import pyperclip

from . import config
from . import vision


def _click_first_match(
    candidates: Sequence[dict],
    *,
    label: str,
    fallback: tuple[int, int] | None = None,
    double_click: bool = False,
) -> tuple[int, int] | None:
    for spec in candidates:
        image_path = spec.get("image")
        if not image_path or not os.path.exists(image_path):
            continue

        box = vision.locate_on_screen(
            image_path,
            confidence=spec.get("confidence", config.IMAGE_CONFIDENCE),
            region=spec.get("region"),
            scales=spec.get("scales"),
        )
        if not box:
            continue

        x, y = pyautogui.center(box)
        dx, dy = spec.get("offset", (0, 0))
        target = (x + dx, y + dy)

        print(f"   {label}: {os.path.basename(image_path)} detectee a {box}, clic sur {target}")
        pyautogui.click(target)
        if double_click:
            time.sleep(0.12)
            pyautogui.click(target)
        return target

    if fallback:
        print(f"   {label}: utilisation du fallback {fallback}")
        pyautogui.click(fallback)
        if double_click:
            time.sleep(0.12)
            pyautogui.click(fallback)
        return fallback

    return None


 


def calibrate_search_region() -> None:
    if config.SEARCH_SCAN_REGION is not None:
        return

    for spec in config.HEADER_TEMPLATES:
        image_path = spec.get("image")
        if not image_path or not os.path.exists(image_path):
            continue

        box = vision.locate_on_screen(
            image_path,
            confidence=spec.get("confidence", 0.7),
            region=None,
            scales=spec.get("scales"),
        )
        if not box:
            continue

        x, y, w, h = box
        padding = spec.get("padding", (0, 0, 0, 120))
        left_pad, top_pad, right_pad, bottom_pad = padding
        config.SEARCH_SCAN_REGION = (
            max(0, x - left_pad),
            max(0, y - top_pad),
            w + left_pad + right_pad,
            h + top_pad + bottom_pad,
        )
        print(f"[INFO] Search region calibrated: {config.SEARCH_SCAN_REGION}")
        return

    print("[WARN] Header template not detected; scanning full screen")


def clear_search_field() -> None:
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.1)
    try:
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.05)
        clipboard_content = pyperclip.paste()
    except Exception as exc:
        print(f"   Clipboard unavailable ({exc}); clearing anyway")
        clipboard_content = ''

    pyautogui.press('delete')

    if clipboard_content and clipboard_content.strip():
        preview = ' '.join(clipboard_content.split())
        if len(preview) > 40:
            preview = preview[:37] + '...'
        print(f"   Previous input removed: '{preview}'")
    else:
        print('   Search field already empty')



def focus_search_field() -> tuple[int, int]:
    calibrate_search_region()
    print("Recherche du champ de recherche...")

    target = _click_first_match(
        config.SEARCH_FIELD_TEMPLATES,
        label="Champ de recherche",
        fallback=config.SEARCH_BAR_FALLBACK,
        double_click=True,
    )
    if not target:
        raise RuntimeError(
            "Champ de recherche introuvable - ajoutez un template ou configurez SEARCH_BAR_FALLBACK"
        )
    time.sleep(0.15)
    clear_search_field()
    return target


def submit_search() -> None:
    pyautogui.press('enter')
    time.sleep(0.2)


 


def open_console_and_close_window() -> None:
    """
    Ouvre la console du navigateur et exécute window.close().
    Utilise les raccourcis clavier pour ouvrir la console développeur et taper window.close().
    """
    try:
        print("Ouverture de la console du navigateur...")
        # Ouvrir la console du navigateur avec Ctrl+Shift+K
        pyautogui.hotkey('ctrl', 'shift', 'k')
        time.sleep(0.5)
        
        print("Exécution de window.close()...")
        # Taper window.close() dans la console
        pyautogui.typewrite('window.close()')
        time.sleep(0.3)
        pyautogui.press('enter')
        time.sleep(0.5)
        
        print("Console ouverte et window.close() exécuté avec succès")
        
    except Exception as exc:
        print(f"Erreur lors de l'ouverture de la console et exécution: {exc}")


__all__ = [
    
    "calibrate_search_region",
    "clear_search_field",
    
    "focus_search_field",
    "submit_search",
    
    "open_console_and_close_window",
]

