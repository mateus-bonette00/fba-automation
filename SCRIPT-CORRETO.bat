@echo off
REM ============================================
REM INSTALADOR COMPLETO - FBA AUTOMATION
REM Windows - Execute como Administrador
REM Versao Correta - Sem instalacao do Git
REM ============================================

color 0A
title Instalador Completo - FBA Automation

echo.
echo ============================================================
echo    INSTALADOR AUTOMATICO COMPLETO - FBA AUTOMATION
echo ============================================================
echo.
echo Este script vai instalar TUDO automaticamente:
echo.
echo   [1] Chocolatey (gerenciador de pacotes Windows)
echo   [2] Python 3.11 (interpretador Python)
echo   [3] Node.js 20 LTS (runtime JavaScript)
echo   [4] Google Chrome (navegador)
echo   [5] Visual C++ Build Tools (para compilar pacotes)
echo   [6] Todas as dependencias Python (FastAPI, Playwright, etc)
echo   [7] Todas as dependencias Node.js (React, Vite, etc)
echo   [8] Navegadores Playwright (Chromium)
echo   [9] Configurar ambiente virtual Python
echo.
echo ============================================================
echo    REQUISITOS IMPORTANTES
echo ============================================================
echo.
echo   - Execute como ADMINISTRADOR (clique direito ^> Executar como admin)
echo   - Tenha conexao com internet ativa
echo   - Tenha pelo menos 2GB de espaco livre
echo   - Aguarde pacientemente (pode demorar 10-15 minutos)
echo.
echo ============================================================
echo.
pause

REM ============================================
REM VERIFICAR PERMISSOES DE ADMINISTRADOR
REM ============================================
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo.
    echo ============================================================
    echo    SOLICITANDO PERMISSOES DE ADMINISTRADOR...
    echo ============================================================
    echo.
    echo Uma janela vai abrir solicitando permissoes.
    echo Clique "Sim" para continuar.
    echo.
    timeout /t 3 /nobreak >nul

    REM Reiniciar como Admin
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b 0
)

echo.
echo [OK] Permissoes de administrador verificadas!
echo.

REM ============================================
REM PASSO 1: INSTALAR CHOCOLATEY
REM ============================================
echo.
echo ============================================================
echo    [1/9] VERIFICANDO/INSTALANDO CHOCOLATEY
echo ============================================================
echo.

where choco >nul 2>&1
if %errorLevel% EQU 0 (
    echo [OK] Chocolatey ja esta instalado!
    choco --version
) else (
    echo [INSTALANDO] Chocolatey (gerenciador de pacotes)...
    echo Aguarde, isso pode demorar 1-2 minutos...
    echo.

    powershell -NoProfile -ExecutionPolicy Bypass -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"

    REM Atualizar variaveis de ambiente
    call refreshenv.cmd 2>nul

    REM Verificar instalacao
    where choco >nul 2>&1
    if %errorLevel% EQU 0 (
        echo.
        echo [OK] Chocolatey instalado com sucesso!
        choco --version
    ) else (
        color 0C
        echo.
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
echo ============================================================
echo    [2/9] VERIFICANDO/INSTALANDO PYTHON 3.11
echo ============================================================
echo.

where python >nul 2>&1
if %errorLevel% EQU 0 (
    echo [OK] Python ja esta instalado!
    python --version
) else (
    echo [INSTALANDO] Python 3.11...
    echo Aguarde, isso pode demorar 2-3 minutos...
    echo.

    choco install python311 -y --force
    call refreshenv.cmd 2>nul

    REM Verificar instalacao
    where python >nul 2>&1
    if %errorLevel% EQU 0 (
        echo.
        echo [OK] Python instalado com sucesso!
        python --version
    ) else (
        color 0C
        echo.
        echo [ERRO] Falha ao instalar Python!
        echo Instale manualmente: https://www.python.org/downloads/
        pause
        exit /b 1
    )
)

REM ============================================
REM PASSO 3: INSTALAR NODE.JS 20 LTS
REM ============================================
echo.
echo ============================================================
echo    [3/9] VERIFICANDO/INSTALANDO NODE.JS 20 LTS
echo ============================================================
echo.

where node >nul 2>&1
if %errorLevel% EQU 0 (
    echo [OK] Node.js ja esta instalado!
    node --version
    npm --version
) else (
    echo [INSTALANDO] Node.js 20 LTS...
    echo Aguarde, isso pode demorar 2-3 minutos...
    echo.

    choco install nodejs-lts -y --force
    call refreshenv.cmd 2>nul

    REM Verificar instalacao
    where node >nul 2>&1
    if %errorLevel% EQU 0 (
        echo.
        echo [OK] Node.js instalado com sucesso!
        node --version
        npm --version
    ) else (
        color 0C
        echo.
        echo [ERRO] Falha ao instalar Node.js!
        echo Instale manualmente: https://nodejs.org/
        pause
        exit /b 1
    )
)

REM ============================================
REM PASSO 4: INSTALAR GOOGLE CHROME
REM ============================================
echo.
echo ============================================================
echo    [4/9] VERIFICANDO/INSTALANDO GOOGLE CHROME
echo ============================================================
echo.

if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    echo [OK] Google Chrome ja esta instalado!
) else (
    if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
        echo [OK] Google Chrome ja esta instalado!
    ) else (
        echo [INSTALANDO] Google Chrome...
        echo Aguarde, isso pode demorar 1-2 minutos...
        echo.

        choco install googlechrome -y --force
        echo.
        echo [OK] Google Chrome instalado!
    )
)

REM ============================================
REM PASSO 5: INSTALAR VISUAL C++ BUILD TOOLS
REM ============================================
echo.
echo ============================================================
echo    [5/9] VERIFICANDO/INSTALANDO BUILD TOOLS
echo ============================================================
echo.

where cl >nul 2>&1
if %errorLevel% EQU 0 (
    echo [OK] Visual C++ Build Tools ja instaladas!
) else (
    echo [INSTALANDO] Visual C++ Build Tools...
    echo (Necessario para compilar algumas dependencias Python)
    echo Aguarde, isso pode demorar 3-5 minutos...
    echo.

    choco install visualstudio2022buildtools -y --force
    choco install visualstudio2022-workload-vctools -y --force
    echo.
    echo [OK] Build Tools instaladas!
)

REM ============================================
REM PASSO 6: CRIAR VIRTUAL ENVIRONMENT PYTHON
REM ============================================
echo.
echo ============================================================
echo    [6/9] CRIANDO VIRTUAL ENVIRONMENT PYTHON
echo ============================================================
echo.

cd /d "%~dp0"

if exist "backend\venv" (
    echo [OK] Virtual environment ja existe!
) else (
    echo [CRIANDO] Virtual environment no backend...
    echo.

    python -m venv backend\venv

    if %errorLevel% EQU 0 (
        echo [OK] Virtual environment criado com sucesso!
    ) else (
        color 0C
        echo.
        echo [ERRO] Falha ao criar virtual environment!
        pause
        exit /b 1
    )
)

REM ============================================
REM PASSO 7: INSTALAR DEPENDENCIAS PYTHON
REM ============================================
echo.
echo ============================================================
echo    [7/9] INSTALANDO DEPENDENCIAS PYTHON
echo ============================================================
echo.
echo Instalando: FastAPI, Uvicorn, Playwright, Pandas, BeautifulSoup4...
echo Aguarde, isso pode demorar 3-5 minutos...
echo.

REM Atualizar pip primeiro
backend\venv\Scripts\python.exe -m pip install --upgrade pip --quiet

REM Instalar dependencias do requirements.txt
backend\venv\Scripts\pip.exe install -r requirements.txt

if %errorLevel% EQU 0 (
    echo.
    echo [OK] Dependencias Python instaladas com sucesso!
    echo.
    echo Pacotes instalados:
    backend\venv\Scripts\pip.exe list
) else (
    color 0C
    echo.
    echo [ERRO] Falha ao instalar dependencias Python!
    echo Verifique o arquivo requirements.txt
    pause
    exit /b 1
)

echo.
echo [INSTALANDO] Navegadores Playwright (Chromium)...
echo Aguarde, isso pode demorar 1-2 minutos...
echo.

backend\venv\Scripts\python.exe -m playwright install chromium

if %errorLevel% EQU 0 (
    echo.
    echo [OK] Playwright e navegadores instalados!
) else (
    echo.
    echo [AVISO] Erro ao instalar navegadores Playwright
    echo Tente manualmente: backend\venv\Scripts\python.exe -m playwright install
)

REM ============================================
REM PASSO 8: INSTALAR DEPENDENCIAS NODE.JS
REM ============================================
echo.
echo ============================================================
echo    [8/9] INSTALANDO DEPENDENCIAS NODE.JS (FRONTEND)
echo ============================================================
echo.

cd frontend

if exist "node_modules" (
    echo [OK] node_modules ja existe!
) else (
    echo [INSTALANDO] React, Vite, React Router...
    echo Aguarde, isso pode demorar 2-4 minutos...
    echo.

    call npm install

    if %errorLevel% EQU 0 (
        echo.
        echo [OK] Dependencias Node.js instaladas com sucesso!
    ) else (
        color 0C
        echo.
        echo [ERRO] Falha ao instalar dependencias Node.js!
        cd ..
        pause
        exit /b 1
    )
)

cd ..

REM ============================================
REM PASSO 9: CONFIGURAR ESTRUTURA DO PROJETO
REM ============================================
echo.
echo ============================================================
echo    [9/9] CONFIGURANDO ESTRUTURA DO PROJETO
echo ============================================================
echo.

if not exist "logs" (
    mkdir logs
    echo [OK] Pasta logs criada!
) else (
    echo [OK] Pasta logs ja existe!
)

if not exist "backend\data" (
    mkdir backend\data
    echo [OK] Pasta backend\data criada!
) else (
    echo [OK] Pasta backend\data ja existe!
)

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
echo   [OK] Chocolatey         - Gerenciador de pacotes
echo   [OK] Python 3.11        - Interpretador Python
echo   [OK] Node.js 20 LTS     - Runtime JavaScript
echo   [OK] Google Chrome      - Navegador web
echo   [OK] Build Tools        - Compilador C++
echo.
echo DEPENDENCIAS INSTALADAS:
echo   [OK] FastAPI            - Framework web Python
echo   [OK] Uvicorn            - Servidor ASGI
echo   [OK] Playwright         - Automacao de navegador
echo   [OK] Pandas             - Analise de dados
echo   [OK] BeautifulSoup4     - Parser HTML
echo   [OK] React              - Biblioteca UI
echo   [OK] Vite               - Build tool
echo   [OK] React Router       - Roteamento React
echo.
echo AMBIENTE CONFIGURADO:
echo   [OK] Virtual Environment Python
echo   [OK] Navegadores Playwright
echo   [OK] Pastas do projeto
echo.
echo ============================================================
echo    O PROJETO ESTA PRONTO PARA USO!
echo ============================================================
echo.
echo DESEJA INICIAR O PROJETO AGORA? (S/N)
set /p resposta=

if /i "%resposta%"=="S" (
    echo.
    echo ============================================================
    echo    INICIANDO PROJETO...
    echo ============================================================
    echo.
    echo [1/3] Iniciando Chrome Debug...
    start "Chrome Debug" cmd /c "%~dp0INICIAR_CHROME_DEBUG.bat"
    timeout /t 5 /nobreak >nul

    echo [2/3] Iniciando Backend (Python/FastAPI)...
    start "Backend - FastAPI" cmd /k "cd /d "%~dp0backend" && venv\Scripts\activate && python main.py"
    timeout /t 4 /nobreak >nul

    echo [3/3] Iniciando Frontend (React/Vite)...
    start "Frontend - React" cmd /k "cd /d "%~dp0frontend" && npm run dev"
    timeout /t 4 /nobreak >nul

    echo.
    echo ============================================================
    echo    SISTEMA INICIADO COM SUCESSO!
    echo ============================================================
    echo.
    echo SERVICOS RODANDO:
    echo   - Chrome Debug (porta 9222)
    echo   - Backend API (porta 8001)
    echo   - Frontend React (porta 5173)
    echo.
    echo ACESSE:
    echo   Frontend:    http://localhost:5173
    echo   Backend API: http://localhost:8001
    echo   Docs API:    http://localhost:8001/docs
    echo.
    echo Abrindo navegador em 3 segundos...
    timeout /t 3 /nobreak >nul
    start http://localhost:5173

    echo.
    echo Sistema aberto no navegador!
    echo Nao feche as janelas do Chrome Debug, Backend e Frontend!

) else (
    echo.
    echo ============================================================
    echo    PROJETO NAO INICIADO
    echo ============================================================
    echo.
    echo Para iniciar o projeto posteriormente, execute:
    echo   - INICIAR_TUDO.bat
    echo.
    echo Ou execute manualmente:
    echo   1. INICIAR_CHROME_DEBUG.bat
    echo   2. backend\venv\Scripts\activate e python backend\main.py
    echo   3. cd frontend e npm run dev
    echo.
)

echo.
echo ============================================================
echo    INSTALACAO E CONFIGURACAO FINALIZADA!
echo ============================================================
echo.
echo Pressione qualquer tecla para sair...
pause >nul
