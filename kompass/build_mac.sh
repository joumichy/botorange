#!/usr/bin/env bash
set -euo pipefail
# Build KompassScraper for macOS using PyInstaller (onedir)
# Requires: Python 3.9+ on a Mac matching client architecture

cd "$(cd "$(dirname "$0")" && pwd)"
echo "=== Building KompassScraper (macOS) ==="

# 1) Create venv if missing
if [ ! -d "venv" ]; then
  echo "[*] Creating virtual environment..."
  python3 -m venv venv
fi
source venv/bin/activate

# 2) Install requirements + pyinstaller
python -m pip install --upgrade pip >/dev/null 2>&1 || true
echo "[*] Installing Python dependencies..."
pip install -r requirements.txt
pip install pyinstaller

# 3) Pre-download Chromium into a local folder to bundle
export PLAYWRIGHT_BROWSERS_PATH="$PWD/playwright-browsers"
mkdir -p "$PLAYWRIGHT_BROWSERS_PATH"
echo "[*] Ensuring Playwright Chromium is installed locally..."
python -m playwright install chromium

# 4) Clean previous dist/build
rm -rf build dist

# 5) Run PyInstaller on run_scrapper.py (entrypoint)
NAME="KompassScraper"
ICON_ARG=""
# If you have an icon, set ICON_ARG="--icon path/to/icon.icns"

echo "[*] Running PyInstaller..."
pyinstaller run_scrapper.py --name "$NAME" --onedir --noconfirm \
  --collect-all playwright \
  --runtime-hook pyi_runtime_hook_playwright.py $ICON_ARG

# 6) Copy Playwright browsers next to the .app to avoid PyInstaller signing issues
echo "[*] Copying Playwright browsers next to the app..."
mkdir -p "dist/$NAME"
cp -R "${PLAYWRIGHT_BROWSERS_PATH}" "dist/$NAME/playwright-browsers"

echo
echo "[OK] Build completed: dist/$NAME/"
echo "To distribute, zip the dist/$NAME folder or create a DMG."
