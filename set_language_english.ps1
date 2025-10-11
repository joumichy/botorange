# Script to change Windows system language to English
# Right-click > Run with PowerShell

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CHANGE LANGUAGE TO ENGLISH" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

try {
    Write-Host "Current language settings:" -ForegroundColor White
    Get-WinUserLanguageList | Format-Table LanguageTag, EnglishName -AutoSize
    Write-Host ""
    
    Write-Host "Changing to English (en-US)..." -ForegroundColor Yellow
    Set-WinUserLanguageList -LanguageList en-US -Force
    
    Write-Host ""
    Write-Host "SUCCESS! Language changed to ENGLISH" -ForegroundColor Green
    Write-Host ""
    Write-Host "New language settings:" -ForegroundColor White
    Get-WinUserLanguageList | Format-Table LanguageTag, EnglishName -AutoSize
    
    # En cas de succès, attendre 1 seconde puis fermer automatiquement
    Write-Host ""
    Write-Host "Closing in 1 second..." -ForegroundColor Gray
    Start-Sleep -Seconds 1
    
} catch {
    Write-Host ""
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Make sure:" -ForegroundColor Yellow
    Write-Host "1. English language pack is installed" -ForegroundColor Gray
    Write-Host "2. You have administrator rights" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Press any key to close..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

