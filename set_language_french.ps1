# Script pour changer la langue système de Windows en Français
# Clic-droit > Exécuter avec PowerShell

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CHANGER LA LANGUE EN FRANÇAIS" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

try {
    Write-Host "Paramètres de langue actuels:" -ForegroundColor White
    Get-WinUserLanguageList | Format-Table LanguageTag, EnglishName -AutoSize
    Write-Host ""
    
    Write-Host "Changement vers Français (fr-FR)..." -ForegroundColor Yellow
    Set-WinUserLanguageList -LanguageList fr-FR -Force
    
    Write-Host ""
    Write-Host "SUCCÈS! Langue changée en FRANÇAIS" -ForegroundColor Green
    Write-Host ""
    Write-Host "Nouveaux paramètres de langue:" -ForegroundColor White
    Get-WinUserLanguageList | Format-Table LanguageTag, EnglishName -AutoSize
    
    # En cas de succès, attendre 1 seconde puis fermer automatiquement
    Write-Host ""
    Write-Host "Fermeture dans 1 seconde..." -ForegroundColor Gray
    Start-Sleep -Seconds 1
    
} catch {
    Write-Host ""
    Write-Host "ERREUR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Assurez-vous que:" -ForegroundColor Yellow
    Write-Host "1. Le pack de langue français est installé" -ForegroundColor Gray
    Write-Host "2. Vous avez les droits administrateur" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Appuyez sur une touche pour fermer..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

