from __future__ import annotations

import sys
import time
import pyautogui


def _is_macos() -> bool:
    return sys.platform == "darwin"


def primary_mod() -> str:
    """Return platform primary modifier: 'command' on macOS, 'ctrl' otherwise."""
    return "command" if _is_macos() else "ctrl"


def alt_mod() -> str:
    """Return platform alt/option modifier: 'option' on macOS, 'alt' otherwise."""
    return "option" if _is_macos() else "alt"


def select_all() -> None:
    pyautogui.hotkey(primary_mod(), "a")


def copy() -> None:
    pyautogui.hotkey(primary_mod(), "c")


def paste() -> None:
    pyautogui.hotkey(primary_mod(), "v")


def open_chrome_console(delay: float = 0.8) -> None:
    """Open Chrome DevTools console with the right shortcut per platform.

    - macOS: Command+Option+J (Console)
    - Windows/Linux: Ctrl+Shift+J (Console)
    Fallback to the DevTools panel (I) if needed.
    """
    try:
        if _is_macos():
            pyautogui.hotkey("command", "option", "j")
        else:
            pyautogui.hotkey("ctrl", "shift", "j")
        time.sleep(delay)
    except Exception:
        # Fallback to opening DevTools (not directly Console)
        if _is_macos():
            pyautogui.hotkey("command", "option", "i")
        else:
            pyautogui.hotkey("ctrl", "shift", "i")
        time.sleep(delay)


__all__ = [
    "primary_mod",
    "alt_mod",
    "select_all",
    "copy",
    "paste",
    "open_chrome_console",
]

