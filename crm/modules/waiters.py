from __future__ import annotations

import os
import time
from typing import Sequence

from . import config
from . import vision




def wait_for_image_on_screen(
    image_path: str,
    *,
    timeout: float = 15.0,
    interval: float = 0.6,
    confidence: float = config.IMAGE_CONFIDENCE,
    region: tuple[int, int, int, int] | None = None,
    scales: Sequence[float] | None = None,
    stop_event=None,
):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if stop_event is not None and stop_event.is_set():
            return None
        box = vision.locate_on_screen(
            image_path,
            confidence=confidence,
            region=region,
            scales=scales,
        )
        if box:
            return box
        time.sleep(interval)
    return None


def wait_for_any_image_on_screen(
    image_paths: Sequence[str],
    *,
    timeout: float = 15.0,
    interval: float = 0.6,
    confidence: float = config.IMAGE_CONFIDENCE,
    region: tuple[int, int, int, int] | None = None,
    scales: Sequence[float] | None = None,
    stop_event=None,
):
    print(f"   Attente de l'image: {image_paths}")
    start = time.time()
    while time.time() - start < timeout:
        if stop_event is not None and stop_event.is_set():
            return None, None
        for idx, path in enumerate(image_paths):
            if not path or not os.path.exists(path):
                continue
            box = vision.locate_on_screen(
                path,
                confidence=confidence,
                region=region,
                scales=scales,
            )
            if box:
                return idx, box
        time.sleep(interval)
    return None, None


__all__ = [
    "wait_for_image_on_screen",
    "wait_for_any_image_on_screen",
]
