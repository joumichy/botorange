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
        # Directly next to the executable (Windows onedir)
        paths.append(os.path.join(exe_dir, "playwright-browsers"))
        # macOS .app: exe_dir = .../MyApp.app/Contents/MacOS
        # Try parent directories to find dist/<NAME>/playwright-browsers
        parent = exe_dir
        for _ in range(4):
            parent = os.path.dirname(parent)
            if not parent or parent == "/":
                break
            paths.append(os.path.join(parent, "playwright-browsers"))
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        paths.append(os.path.join(meipass, "playwright-browsers"))
        paths.append(os.path.join(os.path.dirname(meipass), "playwright-browsers"))
    # Also consider current working directory (dev convenience)
    paths.append(os.path.join(os.getcwd(), "playwright-browsers"))
    return paths


for p in _candidate_dirs():
    if os.path.isdir(p):
        os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", p)
        break
