@echo off
setlocal ENABLEDELAYEDEXPANSION
REM Build CRM executable for Windows using PyInstaller (onedir)

cd /d "%~dp0"
echo === Building CRM (Windows) ===

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

REM 3) Clean previous dist/build
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM 4) Build
set NAME=CRMSearch
set ICON=
echo [*] Running PyInstaller...
pyinstaller run_crm.py --name %NAME% --onedir --noconfirm ^
  --add-data "assets;assets" ^
  --add-data "scripts;scripts" ^
  --hidden-import pyscreeze ^
  --hidden-import PIL.ImageGrab %ICON% || goto :error

echo.
echo [OK] Build completed: dist\%NAME%\

REM Remove license/trial artifacts if present
if exist "dist\%NAME%\license.key" del /q "dist\%NAME%\license.key"
if exist "dist\%NAME%\.trial.json" del /q "dist\%NAME%\.trial.json"
if exist "dist\%NAME%\.trial.bak.json" del /q "dist\%NAME%\.trial.bak.json"
for %%F in ("dist\%NAME%\\.trial*.json") do if exist "%%~fF" del /q "%%~fF"
echo To distribute, zip the dist\%NAME% folder.
goto :end

:error
echo [ERROR] Build failed. See messages above.
exit /b 1

:end
endlocal
