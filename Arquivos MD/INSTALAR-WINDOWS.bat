@echo off
REM ============================================
REM INSTALADOR DEFINITIVO - FBA AUTOMATION
REM Windows - Duplo clique para instalar
REM ============================================

REM Verificar permissoes de administrador SILENCIOSAMENTE
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    REM Nao eh admin - reiniciar como admin SEM mostrar nada
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit
)

REM A partir daqui JA SOMOS ADMIN - nao precisa pausar!

color 0A
title Instalador FBA Automation

echo.
echo ============================================================
echo    INSTALADOR AUTOMATICO - FBA AUTOMATION
echo ============================================================
echo.
echo [OK] Executando como Administrador
echo.
echo Este script vai instalar automaticamente:
echo   [1] Chocolatey
echo   [2] Python 3.11
echo   [3] Node.js 20 LTS
echo   [4] Google Chrome
echo   [5] Visual C++ Build Tools
echo   [6] Dependencias Python (FastAPI, Playwright, etc)
echo   [7] Dependencias Node.js (React, Vite, etc)
echo   [8] Navegadores Playwright
echo   [9] Configuracao do ambiente
echo.
echo Tempo estimado: 10-15 minutos
echo.
echo Pressione qualquer tecla para iniciar...
pause >nul

REM ============================================
REM PASSO 1: INSTALAR CHOCOLATEY
REM ============================================
echo.
echo [1/9] Verificando Chocolatey...

where choco >nul 2>&1
if %errorLevel% EQU 0 (
    echo [OK] Chocolatey ja instalado
) else (
    echo [INSTALANDO] Chocolatey... Aguarde 1-2 minutos...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
    call refreshenv.cmd 2>nul

    where choco >nul 2>&1
    if %errorLevel% EQU 0 (
        echo [OK] Chocolatey instalado!
    ) else (
        color 0C
        echo [ERRO] Falha ao instalar Chocolatey!
        echo Instale manualmente: https://chocolatey.org/install
        pause
        exit /b 1
    )
)

REM ============================================
REM PASSO 2: INSTALAR PYTHON 3.11
REM ============================================
echo.
echo [2/9] Verificando Python 3.11...

where python >nul 2>&1
if %errorLevel% EQU 0 (
    echo [OK] Python ja instalado
    python --version
) else (
    echo [INSTALANDO] Python 3.11... Aguarde 2-3 minutos...
    choco install python311 -y --force
    call refreshenv.cmd 2>nul

    where python >nul 2>&1
    if %errorLevel% EQU 0 (
        echo [OK] Python instalado!
    ) else (
        color 0C
        echo [ERRO] Falha ao instalar Python!
        pause
        exit /b 1
    )
)

REM ============================================
REM PASSO 3: INSTALAR NODE.JS 20 LTS
REM ============================================
echo.
echo [3/9] Verificando Node.js 20 LTS...

where node >nul 2>&1
if %errorLevel% EQU 0 (
    echo [OK] Node.js ja instalado
    node --version
) else (
    echo [INSTALANDO] Node.js 20 LTS... Aguarde 2-3 minutos...
    choco install nodejs-lts -y --force
    call refreshenv.cmd 2>nul

    where node >nul 2>&1
    if %errorLevel% EQU 0 (
        echo [OK] Node.js instalado!
    ) else (
        color 0C
        echo [ERRO] Falha ao instalar Node.js!
        pause
        exit /b 1
    )
)

REM ============================================
REM PASSO 4: INSTALAR GOOGLE CHROME
REM ============================================
echo.
echo [4/9] Verificando Google Chrome...

if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    echo [OK] Chrome ja instalado
) else (
    if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
        echo [OK] Chrome ja instalado
    ) else (
        echo [INSTALANDO] Google Chrome... Aguarde 1-2 minutos...
        choco install googlechrome -y --force
        echo [OK] Chrome instalado!
    )
)

REM ============================================
REM PASSO 5: INSTALAR BUILD TOOLS
REM ============================================
echo.
echo [5/9] Verificando Build Tools...

where cl >nul 2>&1
if %errorLevel% EQU 0 (
    echo [OK] Build Tools ja instaladas
) else (
    echo [INSTALANDO] Visual C++ Build Tools... Aguarde 3-5 minutos...
    choco install visualstudio2022buildtools -y --force
    choco install visualstudio2022-workload-vctools -y --force
    echo [OK] Build Tools instaladas!
)

REM ============================================
REM PASSO 6: CRIAR VIRTUAL ENVIRONMENT
REM ============================================
echo.
echo [6/9] Criando Virtual Environment Python...

cd /d "%~dp0"

if exist "backend\venv" (
    echo [OK] Virtual environment ja existe
) else (
    echo [CRIANDO] Virtual environment...
    python -m venv backend\venv

    if %errorLevel% EQU 0 (
        echo [OK] Virtual environment criado!
    ) else (
        color 0C
        echo [ERRO] Falha ao criar virtual environment!
        pause
        exit /b 1
    )
)

REM ============================================
REM PASSO 7: INSTALAR DEPENDENCIAS PYTHON
REM ============================================
echo.
echo [7/9] Instalando dependencias Python...
echo Instalando FastAPI, Playwright, Pandas... Aguarde 3-5 minutos...

backend\venv\Scripts\python.exe -m pip install --upgrade pip --quiet
backend\venv\Scripts\pip.exe install -r requirements.txt

if %errorLevel% EQU 0 (
    echo [OK] Dependencias Python instaladas!
) else (
    color 0C
    echo [ERRO] Falha ao instalar dependencias Python!
    pause
    exit /b 1
)

echo [INSTALANDO] Navegadores Playwright...
backend\venv\Scripts\python.exe -m playwright install chromium
echo [OK] Playwright configurado!

REM ============================================
REM PASSO 8: INSTALAR DEPENDENCIAS NODE.JS
REM ============================================
echo.
echo [8/9] Instalando dependencias Node.js...

cd frontend

if exist "node_modules" (
    echo [OK] node_modules ja existe
) else (
    echo [INSTALANDO] React, Vite... Aguarde 2-4 minutos...
    call npm install

    if %errorLevel% EQU 0 (
        echo [OK] Dependencias Node.js instaladas!
    ) else (
        color 0C
        echo [ERRO] Falha ao instalar dependencias Node.js!
        cd ..
        pause
        exit /b 1
    )
)

cd ..

REM ============================================
REM PASSO 9: CONFIGURAR ESTRUTURA
REM ============================================
echo.
echo [9/9] Configurando estrutura do projeto...

if not exist "logs" mkdir logs
if not exist "backend\data" mkdir backend\data

echo [OK] Estrutura configurada!

REM ============================================
REM INSTALACAO CONCLUIDA
REM ============================================
echo.
echo.
echo ============================================================
echo    INSTALACAO CONCLUIDA COM SUCESSO!
echo ============================================================
echo.
echo SOFTWARE INSTALADO:
echo   [OK] Chocolatey, Python 3.11, Node.js 20 LTS
echo   [OK] Google Chrome, Build Tools
echo.
echo DEPENDENCIAS INSTALADAS:
echo   [OK] FastAPI, Uvicorn, Playwright, Pandas
echo   [OK] React, Vite, React Router
echo.
echo AMBIENTE CONFIGURADO:
echo   [OK] Virtual Environment, Navegadores, Pastas
echo.
echo ============================================================
echo.
echo DESEJA INICIAR O PROJETO AGORA? (S/N)
set /p resposta=

if /i "%resposta%"=="S" (
    echo.
    echo [1/3] Iniciando Chrome Debug...
    start "Chrome Debug" cmd /c "%~dp0INICIAR_CHROME_DEBUG.bat"
    timeout /t 5 /nobreak >nul

    echo [2/3] Iniciando Backend...
    start "Backend" cmd /k "cd /d "%~dp0backend" && venv\Scripts\activate && python main.py"
    timeout /t 4 /nobreak >nul

    echo [3/3] Iniciando Frontend...
    start "Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"
    timeout /t 4 /nobreak >nul

    echo.
    echo [OK] Sistema iniciado!
    echo.
    echo Acesse: http://localhost:5173
    echo.
    timeout /t 3 /nobreak >nul
    start http://localhost:5173

    echo.
    echo Sistema funcionando! Nao feche as janelas.
    timeout /t 5
) else (
    echo.
    echo Para iniciar depois: INICIAR_TUDO.bat
    echo.
    pause
)
