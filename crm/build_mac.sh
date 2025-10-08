#!/usr/bin/env bash
set -euo pipefail
# Build CRM executable for macOS using PyInstaller (onedir)

cd "$(cd "$(dirname "$0")" && pwd)"
echo "=== Building CRM (macOS) ==="

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

# 3) Clean previous dist/build
rm -rf build dist

# 4) Build
NAME="CRMSearch"
ICON_ARG=""
# If you have an icon, set ICON_ARG="--icon path/to/icon.icns"

echo "[*] Running PyInstaller..."
pyinstaller run_crm.py --name "$NAME" --onedir --noconfirm \
  --add-data "assets:assets" $ICON_ARG

# 5) Create a .command launcher that keeps Terminal open via bash
LAUNCHER="dist/$NAME/Run_CRM.command"
cat > "$LAUNCHER" <<'EOF'
#!/bin/bash
cd "$(cd "$(dirname "$0")" && pwd)"
echo "=== CRM Search ==="
echo
export SHELL=/bin/bash
/bin/bash -lc "./CRMSearch.app/Contents/MacOS/CRMSearch"
status=$?
echo
echo "Process exited with status: $status"
echo "Press Enter to close this window..."
read -r _
exit $status
EOF
chmod +x "$LAUNCHER"

echo
echo "[OK] Build completed: dist/$NAME/"
echo "To distribute, zip the dist/$NAME folder or create a DMG."
