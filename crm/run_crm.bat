@echo off
echo === Recherche CRM Orange ===
echo.

REM Activer l'environnement virtuel si il existe
if exist "venv\Scripts\activate.bat" (
    echo Activation de l'environnement virtuel...
    call venv\Scripts\activate.bat
)

REM Lancer le script
python run_crm.py

echo.
echo Appuyez sur une touche pour fermer...
pause > nul
