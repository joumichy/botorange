@echo off
setlocal ENABLEDELAYEDEXPANSION

echo === Scraper Kompass (Windows) ===
cd /d "%~dp0"
echo.

REM Créer l'environnement virtuel s'il n'existe pas
if not exist "venv" (
    echo [*] Création de l'environnement virtuel...
    python -m venv venv
)

REM Activer l'environnement virtuel
call venv\Scripts\activate.bat

REM Mettre pip à jour (silencieux)
python -m pip install --upgrade pip >nul 2>&1

REM Installer les dépendances
echo [*] Installation des dépendances...
pip install -r requirements.txt || goto :end

REM Installer le navigateur Playwright (Chromium)
echo [*] Installation de Chromium pour Playwright (si nécessaire)...
python -m playwright install chromium || goto :end

echo.
echo [*] Lancement du scraper...
python run_scrapper.py

:end
echo.
echo Appuyez sur une touche pour fermer...
pause > nul
endlocal

