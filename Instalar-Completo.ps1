# ============================================
# INSTALADOR COMPLETO - FBA AUTOMATION
# PowerShell Script - Windows 10/11
# Execute: .\Instalar-Completo.ps1
# ============================================

#Requires -RunAsAdministrator

# Configurações
$ErrorActionPreference = "Continue"
$ProgressPreference = 'SilentlyContinue'

# Cores
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Title {
    param([string]$Title)
    Write-Host ""
    Write-ColorOutput "============================================================" "Cyan"
    Write-ColorOutput "   $Title" "Yellow"
    Write-ColorOutput "============================================================" "Cyan"
    Write-Host ""
}

function Write-Step {
    param([string]$Step)
    Write-ColorOutput "[*] $Step" "Green"
}

function Write-Error {
    param([string]$ErrorMsg)
    Write-ColorOutput "[X] ERRO: $ErrorMsg" "Red"
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "[OK] $Message" "Green"
}

# Banner
Clear-Host
Write-Title "INSTALADOR AUTOMATICO COMPLETO - FBA AUTOMATION"

Write-Host "Este script vai instalar TUDO automaticamente:" -ForegroundColor White
Write-Host ""
Write-Host "  [1] Chocolatey (gerenciador de pacotes)" -ForegroundColor Cyan
Write-Host "  [2] Python 3.11" -ForegroundColor Cyan
Write-Host "  [3] Node.js 20 LTS" -ForegroundColor Cyan
Write-Host "  [4] Google Chrome" -ForegroundColor Cyan
Write-Host "  [5] Git" -ForegroundColor Cyan
Write-Host "  [6] Visual C++ Build Tools" -ForegroundColor Cyan
Write-Host "  [7] Dependencias Python (FastAPI, Playwright, etc)" -ForegroundColor Cyan
Write-Host "  [8] Dependencias Node.js (React, Vite, etc)" -ForegroundColor Cyan
Write-Host "  [9] Navegadores Playwright" -ForegroundColor Cyan
Write-Host "  [10] Configuracao do ambiente" -ForegroundColor Cyan
Write-Host ""
Write-ColorOutput "REQUISITOS:" "Yellow"
Write-Host "  - Execute como Administrador (PowerShell)" -ForegroundColor White
Write-Host "  - Conexao com internet ativa" -ForegroundColor White
Write-Host "  - Pelo menos 2GB de espaco livre" -ForegroundColor White
Write-Host ""

$confirm = Read-Host "Deseja continuar? (S/N)"
if ($confirm -ne "S" -and $confirm -ne "s") {
    Write-ColorOutput "Instalacao cancelada pelo usuario." "Yellow"
    exit
}

# Verificar permissões de administrador
Write-Title "VERIFICANDO PERMISSOES"

$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Error "Este script precisa ser executado como Administrador!"
    Write-Host ""
    Write-Host "Como executar como Administrador:" -ForegroundColor Yellow
    Write-Host "  1. Abra PowerShell como Administrador" -ForegroundColor White
    Write-Host "  2. Execute: Set-ExecutionPolicy Bypass -Scope Process -Force" -ForegroundColor White
    Write-Host "  3. Execute: .\Instalar-Completo.ps1" -ForegroundColor White
    Write-Host ""
    pause
    exit 1
}

Write-Success "Permissoes de administrador verificadas!"

# ============================================
# PASSO 1: INSTALAR CHOCOLATEY
# ============================================
Write-Title "[1/10] VERIFICANDO/INSTALANDO CHOCOLATEY"

$chocoInstalled = Get-Command choco -ErrorAction SilentlyContinue
if ($chocoInstalled) {
    Write-Success "Chocolatey ja esta instalado!"
    choco --version
} else {
    Write-Step "Instalando Chocolatey..."
    Write-Host "Aguarde, isso pode demorar 1-2 minutos..." -ForegroundColor Yellow

    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072

    try {
        Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

        # Recarregar PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

        Write-Success "Chocolatey instalado com sucesso!"
    } catch {
        Write-Error "Falha ao instalar Chocolatey: $_"
        Write-Host "Instale manualmente: https://chocolatey.org/install" -ForegroundColor Yellow
        pause
        exit 1
    }
}

# ============================================
# PASSO 2: INSTALAR PYTHON 3.11
# ============================================
Write-Title "[2/10] VERIFICANDO/INSTALANDO PYTHON 3.11"

$pythonInstalled = Get-Command python -ErrorAction SilentlyContinue
if ($pythonInstalled) {
    Write-Success "Python ja esta instalado!"
    python --version
} else {
    Write-Step "Instalando Python 3.11..."
    Write-Host "Aguarde, isso pode demorar 2-3 minutos..." -ForegroundColor Yellow

    choco install python311 -y --force

    # Recarregar PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

    $pythonInstalled = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonInstalled) {
        Write-Success "Python instalado com sucesso!"
        python --version
    } else {
        Write-Error "Falha ao instalar Python!"
        Write-Host "Instale manualmente: https://www.python.org/downloads/" -ForegroundColor Yellow
        pause
        exit 1
    }
}

# ============================================
# PASSO 3: INSTALAR NODE.JS 20 LTS
# ============================================
Write-Title "[3/10] VERIFICANDO/INSTALANDO NODE.JS 20 LTS"

$nodeInstalled = Get-Command node -ErrorAction SilentlyContinue
if ($nodeInstalled) {
    Write-Success "Node.js ja esta instalado!"
    node --version
    npm --version
} else {
    Write-Step "Instalando Node.js 20 LTS..."
    Write-Host "Aguarde, isso pode demorar 2-3 minutos..." -ForegroundColor Yellow

    choco install nodejs-lts -y --force

    # Recarregar PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

    $nodeInstalled = Get-Command node -ErrorAction SilentlyContinue
    if ($nodeInstalled) {
        Write-Success "Node.js instalado com sucesso!"
        node --version
        npm --version
    } else {
        Write-Error "Falha ao instalar Node.js!"
        Write-Host "Instale manualmente: https://nodejs.org/" -ForegroundColor Yellow
        pause
        exit 1
    }
}

# ============================================
# PASSO 4: INSTALAR GOOGLE CHROME
# ============================================
Write-Title "[4/10] VERIFICANDO/INSTALANDO GOOGLE CHROME"

$chromePath1 = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$chromePath2 = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

if ((Test-Path $chromePath1) -or (Test-Path $chromePath2)) {
    Write-Success "Google Chrome ja esta instalado!"
} else {
    Write-Step "Instalando Google Chrome..."
    Write-Host "Aguarde, isso pode demorar 1-2 minutos..." -ForegroundColor Yellow

    choco install googlechrome -y --force
    Write-Success "Google Chrome instalado!"
}

# ============================================
# PASSO 5: INSTALAR GIT
# ============================================
Write-Title "[5/10] VERIFICANDO/INSTALANDO GIT"

$gitInstalled = Get-Command git -ErrorAction SilentlyContinue
if ($gitInstalled) {
    Write-Success "Git ja esta instalado!"
    git --version
} else {
    Write-Step "Instalando Git..."
    Write-Host "Aguarde, isso pode demorar 1-2 minutos..." -ForegroundColor Yellow

    choco install git -y --force

    # Recarregar PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

    Write-Success "Git instalado!"
}

# ============================================
# PASSO 6: INSTALAR BUILD TOOLS
# ============================================
Write-Title "[6/10] VERIFICANDO/INSTALANDO BUILD TOOLS"

Write-Step "Verificando Visual C++ Build Tools..."

# Verificar se já está instalado
$buildToolsPath = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools"
if (Test-Path $buildToolsPath) {
    Write-Success "Visual C++ Build Tools ja instaladas!"
} else {
    Write-Step "Instalando Visual C++ Build Tools..."
    Write-Host "Aguarde, isso pode demorar 5-10 minutos..." -ForegroundColor Yellow
    Write-Host "(Necessario para compilar algumas dependencias Python)" -ForegroundColor Gray

    choco install visualstudio2022buildtools -y --force
    choco install visualstudio2022-workload-vctools -y --force

    Write-Success "Build Tools instaladas!"
}

# ============================================
# PASSO 7: CRIAR VIRTUAL ENVIRONMENT
# ============================================
Write-Title "[7/10] CRIANDO VIRTUAL ENVIRONMENT PYTHON"

$projectDir = $PSScriptRoot
Set-Location $projectDir

$venvPath = Join-Path $projectDir "backend\venv"

if (Test-Path $venvPath) {
    Write-Success "Virtual environment ja existe!"
} else {
    Write-Step "Criando virtual environment no backend..."

    try {
        python -m venv backend\venv
        Write-Success "Virtual environment criado com sucesso!"
    } catch {
        Write-Error "Falha ao criar virtual environment: $_"
        pause
        exit 1
    }
}

# ============================================
# PASSO 8: INSTALAR DEPENDENCIAS PYTHON
# ============================================
Write-Title "[8/10] INSTALANDO DEPENDENCIAS PYTHON"

Write-Host "Instalando: FastAPI, Uvicorn, Playwright, Pandas, BeautifulSoup4..." -ForegroundColor Yellow
Write-Host "Aguarde, isso pode demorar 3-5 minutos..." -ForegroundColor Yellow
Write-Host ""

$pythonExe = Join-Path $projectDir "backend\venv\Scripts\python.exe"
$pipExe = Join-Path $projectDir "backend\venv\Scripts\pip.exe"

# Atualizar pip
Write-Step "Atualizando pip..."
& $pythonExe -m pip install --upgrade pip --quiet

# Instalar dependências
Write-Step "Instalando dependencias do requirements.txt..."
$requirementsPath = Join-Path $projectDir "requirements.txt"

try {
    & $pipExe install -r $requirementsPath

    Write-Host ""
    Write-Success "Dependencias Python instaladas com sucesso!"
    Write-Host ""
    Write-Step "Pacotes instalados:"
    & $pipExe list
} catch {
    Write-Error "Falha ao instalar dependencias Python: $_"
    pause
    exit 1
}

# Instalar navegadores Playwright
Write-Host ""
Write-Step "Instalando navegadores Playwright (Chromium)..."
Write-Host "Aguarde, isso pode demorar 1-2 minutos..." -ForegroundColor Yellow

try {
    & $pythonExe -m playwright install chromium
    Write-Success "Playwright e navegadores instalados!"
} catch {
    Write-ColorOutput "[!] Aviso: Erro ao instalar navegadores Playwright" "Yellow"
    Write-Host "Tente manualmente: backend\venv\Scripts\python.exe -m playwright install" -ForegroundColor Gray
}

# ============================================
# PASSO 9: INSTALAR DEPENDENCIAS NODE.JS
# ============================================
Write-Title "[9/10] INSTALANDO DEPENDENCIAS NODE.JS (FRONTEND)"

Set-Location (Join-Path $projectDir "frontend")

$nodeModulesPath = "node_modules"

if (Test-Path $nodeModulesPath) {
    Write-Success "node_modules ja existe!"
} else {
    Write-Step "Instalando React, Vite, React Router..."
    Write-Host "Aguarde, isso pode demorar 2-4 minutos..." -ForegroundColor Yellow
    Write-Host ""

    try {
        npm install
        Write-Host ""
        Write-Success "Dependencias Node.js instaladas com sucesso!"
    } catch {
        Write-Error "Falha ao instalar dependencias Node.js: $_"
        Set-Location $projectDir
        pause
        exit 1
    }
}

Set-Location $projectDir

# ============================================
# PASSO 10: CONFIGURAR ESTRUTURA
# ============================================
Write-Title "[10/10] CONFIGURANDO ESTRUTURA DO PROJETO"

# Criar pasta logs
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
    Write-Success "Pasta logs criada!"
} else {
    Write-Success "Pasta logs ja existe!"
}

# Criar pasta backend\data
if (-not (Test-Path "backend\data")) {
    New-Item -ItemType Directory -Path "backend\data" | Out-Null
    Write-Success "Pasta backend\data criada!"
} else {
    Write-Success "Pasta backend\data ja existe!"
}

# ============================================
# INSTALACAO CONCLUIDA
# ============================================
Write-Host ""
Write-Host ""
Write-Title "INSTALACAO CONCLUIDA COM SUCESSO!"

Write-ColorOutput "SOFTWARE INSTALADO:" "Cyan"
Write-Host "  [OK] Chocolatey         - Gerenciador de pacotes" -ForegroundColor Green
Write-Host "  [OK] Python 3.11        - Interpretador Python" -ForegroundColor Green
Write-Host "  [OK] Node.js 20 LTS     - Runtime JavaScript" -ForegroundColor Green
Write-Host "  [OK] Google Chrome      - Navegador web" -ForegroundColor Green
Write-Host "  [OK] Git                - Controle de versao" -ForegroundColor Green
Write-Host "  [OK] Build Tools        - Compilador C++" -ForegroundColor Green
Write-Host ""

Write-ColorOutput "DEPENDENCIAS INSTALADAS:" "Cyan"
Write-Host "  [OK] FastAPI            - Framework web Python" -ForegroundColor Green
Write-Host "  [OK] Uvicorn            - Servidor ASGI" -ForegroundColor Green
Write-Host "  [OK] Playwright         - Automacao de navegador" -ForegroundColor Green
Write-Host "  [OK] Pandas             - Analise de dados" -ForegroundColor Green
Write-Host "  [OK] BeautifulSoup4     - Parser HTML" -ForegroundColor Green
Write-Host "  [OK] React              - Biblioteca UI" -ForegroundColor Green
Write-Host "  [OK] Vite               - Build tool" -ForegroundColor Green
Write-Host "  [OK] React Router       - Roteamento React" -ForegroundColor Green
Write-Host ""

Write-ColorOutput "AMBIENTE CONFIGURADO:" "Cyan"
Write-Host "  [OK] Virtual Environment Python" -ForegroundColor Green
Write-Host "  [OK] Navegadores Playwright" -ForegroundColor Green
Write-Host "  [OK] Pastas do projeto" -ForegroundColor Green
Write-Host ""

Write-Title "O PROJETO ESTA PRONTO PARA USO!"

Write-Host ""
$iniciar = Read-Host "Deseja iniciar o projeto agora? (S/N)"

if ($iniciar -eq "S" -or $iniciar -eq "s") {
    Write-Host ""
    Write-Title "INICIANDO PROJETO..."

    Write-Step "[1/3] Iniciando Chrome Debug..."
    Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "`"$projectDir\INICIAR_CHROME_DEBUG.bat`""
    Start-Sleep -Seconds 5

    Write-Step "[2/3] Iniciando Backend (Python/FastAPI)..."
    Start-Process -FilePath "cmd.exe" -ArgumentList "/k", "cd /d `"$projectDir\backend`" && venv\Scripts\activate && python main.py"
    Start-Sleep -Seconds 4

    Write-Step "[3/3] Iniciando Frontend (React/Vite)..."
    Start-Process -FilePath "cmd.exe" -ArgumentList "/k", "cd /d `"$projectDir\frontend`" && npm run dev"
    Start-Sleep -Seconds 4

    Write-Host ""
    Write-Title "SISTEMA INICIADO COM SUCESSO!"

    Write-ColorOutput "SERVICOS RODANDO:" "Cyan"
    Write-Host "  - Chrome Debug (porta 9222)" -ForegroundColor White
    Write-Host "  - Backend API (porta 8001)" -ForegroundColor White
    Write-Host "  - Frontend React (porta 5173)" -ForegroundColor White
    Write-Host ""

    Write-ColorOutput "ACESSE:" "Cyan"
    Write-Host "  Frontend:    http://localhost:5173" -ForegroundColor Yellow
    Write-Host "  Backend API: http://localhost:8001" -ForegroundColor Yellow
    Write-Host "  Docs API:    http://localhost:8001/docs" -ForegroundColor Yellow
    Write-Host ""

    Write-Step "Abrindo navegador em 3 segundos..."
    Start-Sleep -Seconds 3
    Start-Process "http://localhost:5173"

    Write-Host ""
    Write-Success "Sistema aberto no navegador!"
    Write-ColorOutput "Nao feche as janelas do Chrome Debug, Backend e Frontend!" "Yellow"

} else {
    Write-Host ""
    Write-Title "PROJETO NAO INICIADO"

    Write-Host "Para iniciar o projeto posteriormente, execute:" -ForegroundColor White
    Write-Host "  - INICIAR_TUDO.bat" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Ou execute manualmente:" -ForegroundColor White
    Write-Host "  1. INICIAR_CHROME_DEBUG.bat" -ForegroundColor Cyan
    Write-Host "  2. backend\venv\Scripts\activate e python backend\main.py" -ForegroundColor Cyan
    Write-Host "  3. cd frontend e npm run dev" -ForegroundColor Cyan
}

Write-Host ""
Write-Title "INSTALACAO E CONFIGURACAO FINALIZADA!"

Write-Host ""
Write-Host "Pressione qualquer tecla para sair..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
