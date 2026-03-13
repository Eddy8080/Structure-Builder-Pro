# Structure Builder Pro - Script de Compilação Sênior
Write-Host "Iniciando processo de build..." -ForegroundColor Cyan

# Remove pastas de builds anteriores para garantir limpeza
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }

# Comando PyInstaller
# --add-data "origem;destino" (No Windows usa-se ponto e vírgula)
pyinstaller --noconfirm --onefile --windowed `
    --name "StructureBuilderPro" `
    --icon "logo.ico" `
    --add-data "web;web" `
    --add-data "version.json;." `
    --add-data "manual.html;." `
    bridge.py

Write-Host "Build concluído com sucesso! O executável está na pasta 'dist'." -ForegroundColor Green
