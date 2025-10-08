from __future__ import annotations

import os
from pathlib import Path
import sys
from typing import Sequence

import pyautogui

def _runtime_base_dir() -> Path:
    """Return the application base directory at runtime.

    - Frozen (PyInstaller): dist/<Name>/ (parent of .app on macOS)
    - Dev: repository's crm/ directory
    """
    try:
        if getattr(sys, "frozen", False):
            exe_dir = Path(sys.executable).resolve().parent
            exe_dir_str = str(exe_dir).replace("\\", "/")
            if sys.platform == "darwin" and "/Contents/MacOS" in exe_dir_str:
                return (exe_dir / ".." / ".." / "..").resolve()
            return exe_dir
    except Exception:
        pass
    return Path(__file__).resolve().parent.parent

BASE_DIR = _runtime_base_dir()

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.15

INPUT_FILE = "kompass_data_*.xlsx"

def _get_output_dir() -> str:
    """Return a directory next to the executable/app when frozen.

    - macOS (.app): dist/<Name>/ (parent of the .app bundle)
    - Windows: dist/<Name>/ (folder of the .exe)
    - Dev: project root (crm/)
    """
    try:
        if getattr(sys, "frozen", False):
            exe_dir = Path(sys.executable).resolve().parent
            # macOS .app: .../YourApp.app/Contents/MacOS
            exe_dir_str = str(exe_dir).replace("\\", "/")
            if sys.platform == "darwin" and "/Contents/MacOS" in exe_dir_str:
                return str((exe_dir / ".." / ".." / "..").resolve())
            return str(exe_dir)
    except Exception:
        pass
    return str(BASE_DIR)

OUTPUT_FILE = str(Path(_get_output_dir()) / "crm_results.xlsx")

ASSETS_DIR = (BASE_DIR / "assets").resolve()

def asset(name: str) -> str:
    return str(ASSETS_DIR / name)

SEARCH_BAR_IMAGE = asset("search_loop.png")
CLOSE_BUTTON_IMAGE = asset("close-button.png")
INTERLOCUTOR_BUTTON_IMAGE = asset("interlocutor.png")
INTERLOCUTOR_BUTTON_IMAGE_2 = asset("interlocutor-2.png")
INTERLOCUTOR_BUTTON_IMAGE_3 = asset("interlocutor-3.png")
INTERLOCUTOR_BUTTON_IMAGE_4 = asset("interlocuteur-4.png")
INTERLOCUTOR_BUTTON_IMAGE_5 = asset("interlocuteur-5.png")
LIST_INTERLOCUTOR_IMAGE = asset("list-interlocutors.png")
PRE_FETCH_IMAGE = asset("pre-fetch.png")
PRE_FETCH_IMAGE_2 = asset("pre-fetch-2.png")
NO_RESULT_IMAGE = asset("no-result.png")

RESULT_CANCEL_OK_IMAGE = asset("result-cancel-ok.png")
RESULT_CANCEL_IMAGE = asset("result-cancel.png")
RESULT_OK_IMAGE = asset("result-ok.png")

INTERLOCUTOR_BUTTON_IMAGES: Sequence[str] = (
    INTERLOCUTOR_BUTTON_IMAGE,
    INTERLOCUTOR_BUTTON_IMAGE_2,
    INTERLOCUTOR_BUTTON_IMAGE_3,
    INTERLOCUTOR_BUTTON_IMAGE_4,
    INTERLOCUTOR_BUTTON_IMAGE_5,
)

SEARCH_RESULT_TEMPLATES: Sequence[str] = (
    RESULT_CANCEL_OK_IMAGE,
    RESULT_CANCEL_IMAGE,
    RESULT_OK_IMAGE,
)
SEARCH_PRE_FETCH_TEMPLATES: Sequence[str] = (
    PRE_FETCH_IMAGE,
    PRE_FETCH_IMAGE_2,
)

SEARCH_FIELD_TEMPLATES: Sequence[dict] = (
    {"image": SEARCH_BAR_IMAGE, "offset": (-75, 0), "confidence": 0.78, "scales": (1.0, 0.96, 1.04)},
    {"image": asset("search_loop.png"), "offset": (-95, 0), "confidence": 0.8, "scales": (1.0, 0.97, 1.03)},
    {"image": asset("loop-2.png"), "offset": (-90, 0), "confidence": 0.82},
    {"image": asset("loop.png"), "offset": (-85, 0), "confidence": 0.82},
)



SEARCH_ICON_TEMPLATES: Sequence[dict] = (
    {"image": asset("loop.png"), "confidence": 0.82},
    {"image": asset("loop-2.png"), "confidence": 0.82},
    {"image": asset("search_loop.png"), "confidence": 0.8},
)

HEADER_TEMPLATES: Sequence[dict] = (
    {"image": asset("page_top.png"), "confidence": 0.7},
)

SEARCH_BAR_FALLBACK = (640, 180)
SEARCH_ICON_FALLBACK = (760, 180)
CLOSE_TAB_POSITION = (1200, 30)

IMAGE_CONFIDENCE = 0.85
DEFAULT_SCALES: Sequence[float] = (1.0, 0.97, 1.03, 0.94, 1.06)
SEARCH_SCAN_REGION: tuple[int, int, int, int] | None = None
RESULT_REGION: tuple[int, int, int, int] = (500, 250, 700, 600)

OCR_LANG = "fra"
OCR_CONFIG = "--psm 6"

__all__ = [
    "BASE_DIR",
    "INPUT_FILE",
    "OUTPUT_FILE",
    "ASSETS_DIR",
    "SEARCH_BAR_IMAGE",
    "CLOSE_BUTTON_IMAGE",
    "INTERLOCUTOR_BUTTON_IMAGE",
    "INTERLOCUTOR_BUTTON_IMAGE_2",
    "INTERLOCUTOR_BUTTON_IMAGE_3",
    "INTERLOCUTOR_BUTTON_IMAGE_4",
    "INTERLOCUTOR_BUTTON_IMAGE_5",
    "INTERLOCUTOR_BUTTON_IMAGES",
    "NO_RESULT_IMAGE",
    "SEARCH_FIELD_TEMPLATES",
    "SEARCH_ICON_TEMPLATES",
    "HEADER_TEMPLATES",
    "SEARCH_BAR_FALLBACK",
    "SEARCH_ICON_FALLBACK",
    "CLOSE_TAB_POSITION",
    "IMAGE_CONFIDENCE",
    "DEFAULT_SCALES",
    "SEARCH_SCAN_REGION",
    "RESULT_REGION",
    "OCR_LANG",
    "OCR_CONFIG",
    "LIST_INTERLOCUTOR_IMAGE",
    "RESULT_CANCEL_OK_IMAGE",
    "RESULT_CANCEL_IMAGE",
    "RESULT_OK_IMAGE",
    "SEARCH_RESULT_TEMPLATES",
    "PRE_FETCH_IMAGE",
    "PRE_FETCH_IMAGE_2",
    "SEARCH_PRE_FETCH_TEMPLATES",
]
