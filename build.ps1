# Structure Builder Pro - Script de Compilação Sênior
Write-Host "Iniciando processo de build..." -ForegroundColor Cyan

# Remove pastas de builds anteriores para garantir limpeza
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }

# PASSO ÚNICO: Compilar a Aplicação Principal (Arquitetura Single EXE)
Write-Host "Compilando Aplicação Principal..." -ForegroundColor Cyan
pyinstaller --noconfirm --onefile --windowed `
    --name "StructureBuilderPro" `
    --icon "logo.ico" `
    --add-data "web;web" `
    --add-data "version.json;." `
    --add-data "manual.html;." `
    --collect-all "eel" `
    --collect-all "gevent" `
    --collect-all "gevent-websocket" `
    --hidden-import "pywin32" `
    --hidden-import "win32ctypes" `
    bridge.py

Write-Host "Build do executável concluído com sucesso! O executável está na pasta 'dist'." -ForegroundColor Green

# Verificação para o seu processo manual do Inno Setup
if (Test-Path "dist\StructureBuilderPro.exe") {
    Write-Host "Tudo pronto para a criação manual do instalador via Inno Setup." -ForegroundColor Cyan
    Write-Host "O arquivo .iss já está configurado para gerar a saída em: output_installer" -ForegroundColor White
}

# Compilação do Instalador via Inno Setup
Write-Host "Iniciando compilação do instalador (Inno Setup)..." -ForegroundColor Cyan

$isccPath = "ISCC.exe"
$possiblePaths = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 5\ISCC.exe",
    "${env:ProgramFiles}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles}\Inno Setup 5\ISCC.exe"
)

$foundIscc = $false
if (Get-Command ISCC.exe -ErrorAction SilentlyContinue) {
    $foundIscc = $true
} else {
    foreach ($path in $possiblePaths) {
        if (Test-Path $path) {
            $isccPath = $path
            $foundIscc = $true
            break
        }
    }
}

if ($foundIscc) {
    try {
        & $isccPath "installer_config.iss"
        Write-Host "Instalador gerado com sucesso! Verifique a pasta 'dist'." -ForegroundColor Green
    } catch {
        Write-Host "Aviso: Falha ao executar a compilação do Inno Setup." -ForegroundColor Yellow
    }
} else {
    Write-Host "Aviso: Inno Setup (ISCC.exe) não encontrado. O instalador do Windows não foi gerado." -ForegroundColor Yellow
    Write-Host "Por favor, instale o Inno Setup para gerar o instalador automaticamente." -ForegroundColor Yellow
}
