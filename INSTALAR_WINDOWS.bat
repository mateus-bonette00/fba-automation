@echo off
REM ============================================
REM INSTALADOR AUTOMATICO - FBA AUTOMATION
REM Windows - Duplo Clique para Instalar
REM ============================================

color 0A
title Instalador FBA Automation - Windows

echo.
echo ==========================================
echo    INSTALADOR FBA AUTOMATION - WINDOWS
echo ==========================================
echo.
echo Este script vai instalar:
echo   - Chocolatey (gerenciador de pacotes)
echo   - Python 3.11
echo   - Node.js 20 LTS
echo   - Google Chrome
echo   - Git
echo   - Todas as dependencias do projeto
echo.
echo IMPORTANTE: Este script precisa de permissoes de Administrador!
echo.
pause

REM Verificar se esta rodando como Admin
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo.
    echo ==========================================
    echo ERRO: Execute como Administrador!
    echo ==========================================
    echo.
    echo Como fazer:
    echo 1. Clique com botao direito neste arquivo
    echo 2. Selecione "Executar como administrador"
    echo.
    pause
    exit /b 1
)

echo.
echo [1/8] Verificando Chocolatey...
where choco >nul 2>&1
if %errorLevel% EQU 0 (
    echo [OK] Chocolatey ja esta instalado!
) else (
    echo [INSTALANDO] Chocolatey...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"

    REM Atualizar PATH
    call refreshenv

    where choco >nul 2>&1
    if %errorLevel% EQU 0 (
        echo [OK] Chocolatey instalado com sucesso!
    ) else (
        echo [ERRO] Falha ao instalar Chocolatey!
        pause
        exit /b 1
    )
)

echo.
echo [2/8] Verificando Python...
where python >nul 2>&1
if %errorLevel% EQU 0 (
    python --version
    echo [OK] Python ja esta instalado!
) else (
    echo [INSTALANDO] Python 3.11...
    choco install python311 -y
    call refreshenv

    where python >nul 2>&1
    if %errorLevel% EQU 0 (
        python --version
        echo [OK] Python instalado com sucesso!
    ) else (
        echo [ERRO] Falha ao instalar Python!
        echo Baixe manualmente em: https://www.python.org/downloads/
        pause
        exit /b 1
    )
)

echo.
echo [3/8] Verificando Node.js...
where node >nul 2>&1
if %errorLevel% EQU 0 (
    node --version
    echo [OK] Node.js ja esta instalado!
) else (
    echo [INSTALANDO] Node.js 20 LTS...
    choco install nodejs-lts -y
    call refreshenv

    where node >nul 2>&1
    if %errorLevel% EQU 0 (
        node --version
        echo [OK] Node.js instalado com sucesso!
    ) else (
        echo [ERRO] Falha ao instalar Node.js!
        echo Baixe manualmente em: https://nodejs.org/
        pause
        exit /b 1
    )
)

echo.
echo [4/8] Verificando Google Chrome...
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    echo [OK] Google Chrome ja esta instalado!
) else (
    echo [INSTALANDO] Google Chrome...
    choco install googlechrome -y
    echo [OK] Chrome instalado!
)

echo.
echo [5/8] Verificando Git...
where git >nul 2>&1
if %errorLevel% EQU 0 (
    git --version
    echo [OK] Git ja esta instalado!
) else (
    echo [INSTALANDO] Git...
    choco install git -y
    call refreshenv
    echo [OK] Git instalado!
)

echo.
echo [6/8] Criando Virtual Environment Python...
cd /d "%~dp0"

if exist "backend\venv" (
    echo [OK] Virtual environment ja existe!
) else (
    echo [CRIANDO] Virtual environment...
    python -m venv backend\venv
    if %errorLevel% EQU 0 (
        echo [OK] Virtual environment criado!
    ) else (
        echo [ERRO] Falha ao criar virtual environment!
        pause
        exit /b 1
    )
)

echo.
echo [7/8] Instalando dependencias Python...
echo Isso pode demorar alguns minutos...
backend\venv\Scripts\python.exe -m pip install --upgrade pip --quiet
backend\venv\Scripts\pip.exe install -r requirements.txt

if %errorLevel% EQU 0 (
    echo [OK] Dependencias Python instaladas!
) else (
    echo [ERRO] Falha ao instalar dependencias Python!
    pause
    exit /b 1
)

echo.
echo Instalando navegadores Playwright...
backend\venv\Scripts\python.exe -m playwright install chromium
echo [OK] Playwright configurado!

echo.
echo [8/8] Instalando dependencias Node.js...
cd frontend

if exist "node_modules" (
    echo [OK] node_modules ja existe!
) else (
    echo [INSTALANDO] Dependencias do frontend...
    echo Isso pode demorar alguns minutos...
    call npm install

    if %errorLevel% EQU 0 (
        echo [OK] Dependencias Node.js instaladas!
    ) else (
        echo [ERRO] Falha ao instalar dependencias Node.js!
        pause
        exit /b 1
    )
)

cd ..

echo.
echo ==========================================
echo    INSTALACAO CONCLUIDA COM SUCESSO!
echo ==========================================
echo.
echo Software instalado:
echo   [OK] Chocolatey
echo   [OK] Python 3.11
echo   [OK] Node.js
echo   [OK] Google Chrome
echo   [OK] Git
echo   [OK] Dependencias Python
echo   [OK] Dependencias Node.js
echo.
echo Como iniciar o projeto:
echo   1. Execute: INICIAR_TUDO.bat
echo   2. Aguarde todos os servicos iniciarem
echo   3. Acesse http://localhost:5173
echo.
echo Deseja iniciar o projeto agora? (S/N)
set /p resposta=

if /i "%resposta%"=="S" (
    echo.
    echo Iniciando projeto...
    start "" "%~dp0INICIAR_TUDO.bat"
) else (
    echo.
    echo Projeto nao iniciado.
    echo Execute INICIAR_TUDO.bat quando quiser iniciar.
)

echo.
echo Pressione qualquer tecla para sair...
pause >nul
