# ============================================
# Script de Instalação Completa - Windows
# FBA Automation Project
# ============================================

# Executar como Administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "ERRO: Execute este script como Administrador!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Como executar como Administrador:" -ForegroundColor Yellow
    Write-Host "1. Clique com botao direito em PowerShell" -ForegroundColor Yellow
    Write-Host "2. Selecione 'Executar como Administrador'" -ForegroundColor Yellow
    Write-Host "3. Execute este script novamente" -ForegroundColor Yellow
    Write-Host ""
    pause
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  INSTALACAO FBA AUTOMATION - WINDOWS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Este script vai instalar:" -ForegroundColor White
Write-Host "  - Chocolatey (gerenciador de pacotes)" -ForegroundColor Gray
Write-Host "  - Python 3.11" -ForegroundColor Gray
Write-Host "  - Node.js 20 LTS" -ForegroundColor Gray
Write-Host "  - Google Chrome" -ForegroundColor Gray
Write-Host "  - Git" -ForegroundColor Gray
Write-Host "  - Todas as dependencias do projeto" -ForegroundColor Gray
Write-Host ""

$continue = Read-Host "Deseja continuar? (S/N)"
if ($continue -ne "S" -and $continue -ne "s") {
    Write-Host "Instalacao cancelada." -ForegroundColor Yellow
    exit 0
}

# ============================================
# Funcao para verificar se um comando existe
# ============================================
function Test-CommandExists {
    param($command)
    $null = Get-Command $command -ErrorAction SilentlyContinue
    return $?
}

# ============================================
# 1. INSTALAR CHOCOLATEY
# ============================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "1. Instalando Chocolatey..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if (Test-CommandExists choco) {
    Write-Host "Chocolatey ja esta instalado!" -ForegroundColor Green
} else {
    Write-Host "Instalando Chocolatey..." -ForegroundColor Yellow
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

    # Atualizar PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

    if (Test-CommandExists choco) {
        Write-Host "Chocolatey instalado com sucesso!" -ForegroundColor Green
    } else {
        Write-Host "ERRO: Falha ao instalar Chocolatey!" -ForegroundColor Red
        pause
        exit 1
    }
}

# ============================================
# 2. INSTALAR PYTHON 3.11
# ============================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "2. Instalando Python 3.11..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if (Test-CommandExists python) {
    $pythonVersion = python --version 2>&1
    Write-Host "Python ja esta instalado: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "Instalando Python 3.11..." -ForegroundColor Yellow
    choco install python311 -y

    # Atualizar PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

    if (Test-CommandExists python) {
        $pythonVersion = python --version 2>&1
        Write-Host "Python instalado com sucesso: $pythonVersion" -ForegroundColor Green
    } else {
        Write-Host "ERRO: Falha ao instalar Python!" -ForegroundColor Red
        Write-Host "Tente instalar manualmente em: https://www.python.org/downloads/" -ForegroundColor Yellow
        pause
        exit 1
    }
}

# Atualizar pip
Write-Host "Atualizando pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet

# ============================================
# 3. INSTALAR NODE.JS
# ============================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "3. Instalando Node.js..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if (Test-CommandExists node) {
    $nodeVersion = node --version 2>&1
    Write-Host "Node.js ja esta instalado: $nodeVersion" -ForegroundColor Green
} else {
    Write-Host "Instalando Node.js 20 LTS..." -ForegroundColor Yellow
    choco install nodejs-lts -y

    # Atualizar PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

    if (Test-CommandExists node) {
        $nodeVersion = node --version 2>&1
        Write-Host "Node.js instalado com sucesso: $nodeVersion" -ForegroundColor Green
    } else {
        Write-Host "ERRO: Falha ao instalar Node.js!" -ForegroundColor Red
        Write-Host "Tente instalar manualmente em: https://nodejs.org/" -ForegroundColor Yellow
        pause
        exit 1
    }
}

# ============================================
# 4. INSTALAR GOOGLE CHROME
# ============================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "4. Instalando Google Chrome..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
if (Test-Path $chromePath) {
    Write-Host "Google Chrome ja esta instalado!" -ForegroundColor Green
} else {
    Write-Host "Instalando Google Chrome..." -ForegroundColor Yellow
    choco install googlechrome -y

    if (Test-Path $chromePath) {
        Write-Host "Google Chrome instalado com sucesso!" -ForegroundColor Green
    } else {
        Write-Host "AVISO: Chrome nao foi detectado, mas pode estar instalado em outro local." -ForegroundColor Yellow
    }
}

# ============================================
# 5. INSTALAR GIT
# ============================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "5. Instalando Git..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if (Test-CommandExists git) {
    $gitVersion = git --version 2>&1
    Write-Host "Git ja esta instalado: $gitVersion" -ForegroundColor Green
} else {
    Write-Host "Instalando Git..." -ForegroundColor Yellow
    choco install git -y

    # Atualizar PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

    if (Test-CommandExists git) {
        $gitVersion = git --version 2>&1
        Write-Host "Git instalado com sucesso: $gitVersion" -ForegroundColor Green
    } else {
        Write-Host "AVISO: Git nao foi detectado. Pode ser necessario reiniciar o terminal." -ForegroundColor Yellow
    }
}

# ============================================
# 6. INSTALAR DEPENDENCIAS PYTHON
# ============================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "6. Instalando dependencias Python..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$projectDir = $PSScriptRoot
Set-Location $projectDir

# Criar virtual environment
Write-Host "Criando virtual environment..." -ForegroundColor Yellow
if (Test-Path "backend\venv") {
    Write-Host "Virtual environment ja existe." -ForegroundColor Green
} else {
    python -m venv backend\venv
    if ($?) {
        Write-Host "Virtual environment criado!" -ForegroundColor Green
    } else {
        Write-Host "ERRO ao criar virtual environment!" -ForegroundColor Red
        pause
        exit 1
    }
}

# Ativar venv e instalar dependencias
Write-Host "Instalando dependencias Python (pode demorar alguns minutos)..." -ForegroundColor Yellow
& "$projectDir\backend\venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
& "$projectDir\backend\venv\Scripts\pip.exe" install -r requirements.txt

if ($?) {
    Write-Host "Dependencias Python instaladas com sucesso!" -ForegroundColor Green
} else {
    Write-Host "ERRO ao instalar dependencias Python!" -ForegroundColor Red
    pause
    exit 1
}

# Instalar Playwright browsers
Write-Host "Instalando navegadores do Playwright..." -ForegroundColor Yellow
& "$projectDir\backend\venv\Scripts\python.exe" -m playwright install chromium

if ($?) {
    Write-Host "Playwright configurado com sucesso!" -ForegroundColor Green
} else {
    Write-Host "AVISO: Erro ao instalar navegadores Playwright." -ForegroundColor Yellow
}

# ============================================
# 7. INSTALAR DEPENDENCIAS NODE.JS
# ============================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "7. Instalando dependencias Node.js..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Set-Location "$projectDir\frontend"

if (Test-Path "node_modules") {
    Write-Host "node_modules ja existe." -ForegroundColor Green
    $reinstall = Read-Host "Deseja reinstalar? (S/N)"
    if ($reinstall -eq "S" -or $reinstall -eq "s") {
        Write-Host "Instalando dependencias do frontend..." -ForegroundColor Yellow
        npm install
    }
} else {
    Write-Host "Instalando dependencias do frontend (pode demorar alguns minutos)..." -ForegroundColor Yellow
    npm install
}

if ($?) {
    Write-Host "Dependencias Node.js instaladas com sucesso!" -ForegroundColor Green
} else {
    Write-Host "ERRO ao instalar dependencias Node.js!" -ForegroundColor Red
    pause
    exit 1
}

Set-Location $projectDir

# ============================================
# 8. CRIAR SCRIPTS DE INICIALIZACAO
# ============================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "8. Criando scripts de inicializacao..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Script para iniciar Chrome Debug
$chromeDebugScript = @'
@echo off
echo ==========================================
echo Iniciando Chrome Debug...
echo ==========================================
echo.

REM Matar processos na porta 9222
for /f "tokens=5" %%a in ('netstat -aon ^| find ":9222" ^| find "LISTENING"') do taskkill /F /PID %%a 2>nul

REM Aguardar 2 segundos
timeout /t 2 /nobreak >nul

REM Encontrar caminho do Chrome
set CHROME_PATH=
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe
) else (
    echo ERRO: Google Chrome nao encontrado!
    echo Por favor, instale o Google Chrome.
    pause
    exit /b 1
)

REM Criar pasta temporaria
if not exist "%TEMP%\chrome-debug-profile" mkdir "%TEMP%\chrome-debug-profile"

echo Iniciando Chrome na porta 9222...
echo.
echo IMPORTANTE: Use ESTE Chrome para abrir as abas dos produtos!
echo.

start "" "%CHROME_PATH%" --remote-debugging-port=9222 --user-data-dir="%TEMP%\chrome-debug-profile" --disable-extensions --no-first-run --no-default-browser-check "data:text/html,<html><head><title>CHROME DEBUG - ABRA SEUS PRODUTOS AQUI!</title><style>body{margin:0;padding:0;font-family:Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%%,#764ba2 100%%);color:white;display:flex;justify-content:center;align-items:center;min-height:100vh;text-align:center}.container{max-width:700px;padding:40px}h1{font-size:48px;margin-bottom:20px;text-shadow:2px 2px 4px rgba(0,0,0,0.3)}.badge{background:rgba(255,255,255,0.2);padding:15px 30px;border-radius:50px;font-size:20px;font-weight:bold;margin:20px 0;display:inline-block}.instructions{background:rgba(0,0,0,0.2);padding:30px;border-radius:15px;margin-top:30px;text-align:left}.step{margin:15px 0;font-size:18px}.warning{background:rgba(255,193,7,0.3);padding:20px;border-radius:10px;margin-top:20px;border-left:5px solid #ffc107}</style></head><body><div class='container'><h1>CHROME DEBUG</h1><div class='badge'>Conectado na porta 9222</div><div class='instructions'><h2>Como usar:</h2><div class='step'>1. Abra NOVAS ABAS neste Chrome (Ctrl+T)</div><div class='step'>2. Cole as URLs dos produtos</div><div class='step'>3. Volte para http://localhost:5173/capture</div><div class='step'>4. Clique em Capturar Abas</div></div><div class='warning'><strong>IMPORTANTE:</strong><br>Use APENAS este Chrome!<br>Se usar outro, a captura nao funciona.</div></div></body></html>"

timeout /t 3 /nobreak >nul
echo Chrome Debug iniciado com sucesso!
echo.
echo Pressione qualquer tecla para fechar este terminal...
pause >nul
'@

$chromeDebugScript | Out-File -FilePath "iniciar_chrome_debug.bat" -Encoding ASCII

# Script para iniciar tudo
$iniciarTudoScript = @'
@echo off
echo ==========================================
echo INICIANDO FBA AUTOMATION COMPLETO
echo ==========================================
echo.

REM Obter diretorio do script
set PROJECT_DIR=%~dp0
cd /d "%PROJECT_DIR%"

echo 1. Iniciando Chrome Debug...
start "Chrome Debug" cmd /c "%PROJECT_DIR%iniciar_chrome_debug.bat"

timeout /t 5 /nobreak >nul

echo.
echo 2. Iniciando Backend...
start "Backend" cmd /k "cd /d "%PROJECT_DIR%backend" && venv\Scripts\activate && python main.py"

timeout /t 3 /nobreak >nul

echo.
echo 3. Iniciando Frontend...
start "Frontend" cmd /k "cd /d "%PROJECT_DIR%frontend" && npm run dev"

timeout /t 3 /nobreak >nul

echo.
echo ==========================================
echo SISTEMA INICIADO COM SUCESSO!
echo ==========================================
echo.
echo Servicos rodando:
echo   Frontend:     http://localhost:5173
echo   Backend API:  http://localhost:8001
echo   Docs API:     http://localhost:8001/docs
echo   Chrome Debug: porta 9222
echo.
echo Proximo passo:
echo   1. Acesse http://localhost:5173
echo   2. Use o Chrome que foi aberto (roxa)
echo   3. Abra as abas dos produtos
echo   4. Volte ao frontend e clique em Capturar
echo.
echo Pressione qualquer tecla para abrir o navegador...
pause >nul

start http://localhost:5173
'@

$iniciarTudoScript | Out-File -FilePath "iniciar_tudo.bat" -Encoding ASCII

Write-Host "Scripts criados:" -ForegroundColor Green
Write-Host "  - iniciar_chrome_debug.bat" -ForegroundColor Gray
Write-Host "  - iniciar_tudo.bat" -ForegroundColor Gray

# ============================================
# CONCLUSAO
# ============================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  INSTALACAO CONCLUIDA COM SUCESSO!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Software instalado:" -ForegroundColor White
Write-Host "  [OK] Chocolatey" -ForegroundColor Green
Write-Host "  [OK] Python 3.11" -ForegroundColor Green
Write-Host "  [OK] Node.js" -ForegroundColor Green
Write-Host "  [OK] Google Chrome" -ForegroundColor Green
Write-Host "  [OK] Git" -ForegroundColor Green
Write-Host "  [OK] Dependencias Python" -ForegroundColor Green
Write-Host "  [OK] Dependencias Node.js" -ForegroundColor Green
Write-Host ""
Write-Host "Como iniciar o projeto:" -ForegroundColor Cyan
Write-Host "  1. Execute: iniciar_tudo.bat" -ForegroundColor Yellow
Write-Host "  2. Aguarde todos os servicos iniciarem" -ForegroundColor Yellow
Write-Host "  3. Use o Chrome ROXO para abrir produtos" -ForegroundColor Yellow
Write-Host "  4. Acesse http://localhost:5173/capture" -ForegroundColor Yellow
Write-Host ""
Write-Host "Deseja iniciar o projeto agora? (S/N)" -ForegroundColor Cyan
$start = Read-Host

if ($start -eq "S" -or $start -eq "s") {
    Write-Host ""
    Write-Host "Iniciando projeto..." -ForegroundColor Green
    Start-Process "iniciar_tudo.bat"
} else {
    Write-Host ""
    Write-Host "Projeto nao iniciado. Execute 'iniciar_tudo.bat' quando quiser iniciar." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Pressione qualquer tecla para sair..." -ForegroundColor Gray
pause
