from __future__ import annotations

import os
from typing import Sequence

import cv2
import numpy as np
import pyautogui

from . import config

_TEMPLATE_CACHE: dict[str, np.ndarray | None] = {}


def load_template(image_path: str) -> np.ndarray | None:
    if image_path in _TEMPLATE_CACHE:
        return _TEMPLATE_CACHE[image_path]
    if not os.path.exists(image_path):
        print(f"[WARN] Template introuvable: {image_path}")
        _TEMPLATE_CACHE[image_path] = None
        return None
    template = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if template is None:
        print(f"[WARN] Lecture OpenCV impossible pour {image_path}")
    _TEMPLATE_CACHE[image_path] = template
    return template


def locate_with_opencv(
    image_path: str,
    confidence: float,
    *,
    region: tuple[int, int, int, int] | None = None,
    scales: Sequence[float] | None = None,
) -> tuple[int, int, int, int] | None:
    template = load_template(image_path)
    if template is None:
        return None

    capture_region = region or config.SEARCH_SCAN_REGION
    screenshot = pyautogui.screenshot(region=capture_region).convert("RGB")
    screen_gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)

    candidate_scales = scales or config.DEFAULT_SCALES
    best_match: tuple[float, tuple[int, int, int, int]] | None = None

    for scale in candidate_scales:
        if abs(scale - 1.0) < 1e-3:
            templ = template
        else:
            templ_w = max(1, int(template.shape[1] * scale))
            templ_h = max(1, int(template.shape[0] * scale))
            templ = cv2.resize(template, (templ_w, templ_h), interpolation=cv2.INTER_LINEAR)

        if templ.shape[0] > screen_gray.shape[0] or templ.shape[1] > screen_gray.shape[1]:
            continue

        result = cv2.matchTemplate(screen_gray, templ, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val < confidence:
            continue

        x, y = max_loc
        if capture_region:
            x += capture_region[0]
            y += capture_region[1]

        box = (x, y, templ.shape[1], templ.shape[0])
        if not best_match or max_val > best_match[0]:
            best_match = (max_val, box)

    return best_match[1] if best_match else None


def locate_on_screen(
    image_path: str | None,
    *,
    confidence: float = config.IMAGE_CONFIDENCE,
    region: tuple[int, int, int, int] | None = None,
    scales: Sequence[float] | None = None,
) -> tuple[int, int, int, int] | None:
    if not image_path:
        return None

    box = locate_with_opencv(
        image_path,
        confidence,
        region=region,
        scales=scales,
    )
    if box:
        return box

    if not os.path.exists(image_path):
        return None

    try:
        return pyautogui.locateOnScreen(image_path, region=region)
    except Exception as exc:
        print(f"[WARN] locateOnScreen a echoue pour {image_path}: {exc}")
        return None


__all__ = [
    "load_template",
    "locate_with_opencv",
    "locate_on_screen",
]
