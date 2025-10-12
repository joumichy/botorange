@echo off
REM Script batch pour builder CRM et Kompass
REM Double-cliquez pour exécuter
REM Usage: build_all.bat [--zip]

setlocal enabledelayedexpansion

REM Vérifier si l'argument --zip est passé
set "CREATE_ZIP=0"
if /I "%~1"=="--zip" set "CREATE_ZIP=1"

echo.
echo ========================================
echo   BUILD ALL PROJECTS
if "%CREATE_ZIP%"=="1" (
    echo   ^(with ZIP compression^)
)
echo ========================================
echo.

REM Build CRM
echo [1/2] Building CRM...
echo --------------------------------------
echo.
call .\crm\build_win.bat
set CRM_ERROR=%ERRORLEVEL%

if %CRM_ERROR% EQU 0 (
    echo.
    echo [SUCCESS] CRM build completed successfully!
    echo.
    
    REM Build Kompass
    echo [2/2] Building Kompass...
    echo --------------------------------------
    echo.
    call .\kompass\build_win.bat
    set KOMPASS_ERROR=!ERRORLEVEL!
    
    if !KOMPASS_ERROR! EQU 0 (
        echo.
        echo ========================================
        echo [SUCCESS] ALL BUILDS COMPLETED!
        echo ========================================
        echo.
        
        REM Créer les archives ZIP si demandé
        if "%CREATE_ZIP%"=="1" (
            echo.
            echo [3/3] Creating ZIP archives...
            echo --------------------------------------
            echo.
            
            REM Créer le nom de fichier avec la date
            for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
            set TIMESTAMP=!datetime:~0,8!_!datetime:~8,6!
            
            REM Compresser CRM
            echo Compressing CRM...
            powershell -Command "Compress-Archive -Path '.\crm\dist\CRMSearch' -DestinationPath '.\CRMSearch_!TIMESTAMP!.zip' -Force"
            if !ERRORLEVEL! EQU 0 (
                echo [SUCCESS] CRM archive created: CRMSearch_!TIMESTAMP!.zip
            ) else (
                echo [WARNING] Failed to create CRM archive
            )
            
            echo.
            
            REM Compresser Kompass
            echo Compressing Kompass...
            powershell -Command "Compress-Archive -Path '.\kompass\dist\KompassScraper' -DestinationPath '.\KompassScraper_!TIMESTAMP!.zip' -Force"
            if !ERRORLEVEL! EQU 0 (
                echo [SUCCESS] Kompass archive created: KompassScraper_!TIMESTAMP!.zip
            ) else (
                echo [WARNING] Failed to create Kompass archive
            )
            
            echo.
            echo ========================================
            echo [SUCCESS] ALL ARCHIVES CREATED!
            echo ========================================
            echo.
        )
    ) else (
        echo.
        echo ========================================
        echo [ERROR] Kompass build failed!
        echo ========================================
        echo.
        
        REM Afficher les warnings PyInstaller si disponibles
        if exist ".\kompass\build\warn-KompassScraper.txt" (
            echo.
            echo --- PyInstaller Warnings ---
            type ".\kompass\build\warn-KompassScraper.txt"
            echo.
            echo --- End of Warnings ---
            echo.
        )
        
        pause
        exit /b 1
    )
) else (
    echo.
    echo ========================================
    echo [ERROR] CRM build failed! Skipping Kompass build.
    echo ========================================
    echo.
    
    REM Afficher les warnings PyInstaller si disponibles
    if exist ".\crm\build\warn-CRMSearch.txt" (
        echo.
        echo --- PyInstaller Warnings ---
        type ".\crm\build\warn-CRMSearch.txt"
        echo.
        echo --- End of Warnings ---
        echo.
    )
    
    pause
    exit /b 1
)

echo.
echo Press any key to close...
pause > nul

