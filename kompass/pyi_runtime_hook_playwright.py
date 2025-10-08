"""
PyInstaller runtime hook to prefer a bundled Playwright browsers folder.

If a directory named 'playwright-browsers' sits next to the executable
or the PyInstaller extraction directory, set PLAYWRIGHT_BROWSERS_PATH
so Playwright uses it without downloading at client runtime.
"""
import os
import sys


def _candidate_dirs():
    # PyInstaller: onefile uses _MEIPASS; onedir uses the exe dir.
    paths = []
    exe_dir = os.path.dirname(getattr(sys, "executable", ""))
    if exe_dir:
        paths.append(os.path.join(exe_dir, "playwright-browsers"))
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        paths.append(os.path.join(meipass, "playwright-browsers"))
        # In some layouts, browsers may be one level up
        paths.append(os.path.join(os.path.dirname(meipass), "playwright-browsers"))
    # Also consider current working directory (dev convenience)
    paths.append(os.path.join(os.getcwd(), "playwright-browsers"))
    return paths


for p in _candidate_dirs():
    if os.path.isdir(p):
        os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", p)
        break

