@echo off
REM Script to change system language to English
REM Double-click to execute

echo.
echo Starting language change to ENGLISH...
echo.
powershell.exe -ExecutionPolicy Bypass -File "%~dp0set_language_english.ps1"

