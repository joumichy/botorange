@echo off
setlocal ENABLEDELAYEDEXPANSION
REM Build KompassScraper for Windows using PyInstaller (onedir)
REM Requires: Python 3.9+ on Windows build machine

cd /d "%~dp0"
echo === Building KompassScraper (Windows) ===

REM 1) Create venv if missing
if not exist "venv" (
  echo [*] Creating virtual environment...
  python -m venv venv || goto :error
)

call venv\Scripts\activate.bat

REM 2) Install requirements + pyinstaller
python -m pip install --upgrade pip >nul 2>&1
echo [*] Installing Python dependencies...
pip install -r requirements.txt || goto :error
pip install pyinstaller || goto :error

REM 3) Pre-download Chromium into a local folder to bundle
set PLAYWRIGHT_BROWSERS_PATH=%CD%\playwright-browsers
if not exist "%PLAYWRIGHT_BROWSERS_PATH%" (
  mkdir "%PLAYWRIGHT_BROWSERS_PATH%" 2>nul
)
echo [*] Ensuring Playwright Chromium is installed locally...
python -m playwright install chromium || goto :error

REM 4) Clean previous dist/build
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM 5) Run PyInstaller on run_scrapper.py (entrypoint)
set NAME=KompassScraper
set ICON=
REM If you have an icon file, set ICON to: --icon path\to\icon.ico

echo [*] Running PyInstaller...
pyinstaller run_scrapper.py --name %NAME% --onedir --noconfirm ^
  --collect-all playwright ^
  --add-data "playwright-browsers;playwright-browsers" ^
  --runtime-hook pyi_runtime_hook_playwright.py %ICON% || goto :error

echo.
echo [OK] Build completed: dist\%NAME%\
echo To distribute, zip the dist\%NAME% folder.
goto :end

:error
echo [ERROR] Build failed. See messages above.
exit /b 1

:end
endlocal
