#!/bin/bash
# macOS launcher for Kompass scraper

set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "=== Scraper Kompass (macOS) ==="

# Create venv if missing
if [ ! -d "venv" ]; then
  echo "[*] Creating virtual environment..."
  python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Upgrade pip quietly
python -m pip install --upgrade pip >/dev/null 2>&1 || true

echo "[*] Installing dependencies..."
pip install -r requirements.txt

echo "[*] Installing Chromium for Playwright (if needed)..."
python -m playwright install chromium

echo
echo "[*] Starting scraper..."
python3 run_scrapper.py

echo
read -n 1 -s -r -p "Press any key to exit"
echo

