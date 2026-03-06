# Script de Build Automatizado v2.1 - Structure Builder Pro
# Este script gera o .exe e compila o Instalador (Inno Setup) automaticamente

Set-Location $PSScriptRoot

Write-Host "Limpando builds anteriores..." -ForegroundColor Gray
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "output_installer") { Remove-Item -Recurse -Force "output_installer" }

Write-Host "1. Iniciando PyInstaller (Gerando executável profissional)..." -ForegroundColor Cyan

# Comando do PyInstaller configurado para incluir todos os recursos essenciais utilizando o venv (Python 3.12)
$pyinstaller = ".\venv\Scripts\pyinstaller.exe"
$buildCmd = "$pyinstaller --onefile --noconsole --icon='logo.ico' --name='StructureBuilderPro' --add-data 'web;web' --add-data 'manual.html;.' --add-data 'logo.ico;.' --add-data 'venv/Lib/site-packages/eel/eel.js;eel' bridge.py"

# Executa o PyInstaller
Invoke-Expression $buildCmd

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nSucesso! Executável gerado em 'dist/StructureBuilderPro.exe'" -ForegroundColor Green
    
    Write-Host "`n2. Iniciando Inno Setup (Gerando Instalador final)..." -ForegroundColor Cyan
    
    # Caminho padrão do compilador Inno Setup
    $innoCompiler = "C:\Users\edilson.monteiro\AppData\Local\Programs\Inno Setup 6\ISCC.exe"
    
    if (Test-Path $innoCompiler) {
        & $innoCompiler "installer_config.iss"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`nPROCESSO CONCLUÍDO COM SUCESSO!" -ForegroundColor Green
            Write-Host "O Instalador final está pronto na pasta 'output_installer/'" -ForegroundColor Yellow
        } else {
            Write-Host "`nErro durante a compilação do instalador Inno Setup." -ForegroundColor Red
        }
    } else {
        Write-Host "`nCompilador Inno Setup (ISCC.exe) não encontrado em: $innoCompiler" -ForegroundColor Red
        Write-Host "Por favor, verifique se o Inno Setup 6 está instalado no caminho padrão." -ForegroundColor Gray
    }
} else {
    Write-Host "`nOcorreu um erro durante a criação do executável pelo PyInstaller." -ForegroundColor Red
}
