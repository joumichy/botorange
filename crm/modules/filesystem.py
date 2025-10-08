from __future__ import annotations

import glob
import os
from pathlib import Path

from . import config


def find_latest_kompass_file() -> str | None:
    files = glob.glob(config.INPUT_FILE)
    if not files:
        print("Aucun fichier kompass_data_*.xlsx trouve")
        return None
    latest_file = max(files, key=os.path.getmtime)
    print(f"Fichier trouve: {latest_file}")
    return latest_file

__all__ = [
    "find_latest_kompass_file",
]
