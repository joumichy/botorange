@echo off
REM Script pour changer la langue système en français
REM Double-cliquez pour exécuter

echo.
echo Demarrage du changement de langue vers FRANÇAIS...
echo.
powershell.exe -ExecutionPolicy Bypass -File "%~dp0set_language_french.ps1"

