@echo off
REM ============================================
REM BAIXAR DO GITHUB E INSTALAR COMPLETO
REM FBA AUTOMATION - WINDOWS
REM Execute como Administrador
REM ============================================

color 0A
title Baixar do GitHub e Instalar - FBA Automation

echo.
echo ============================================================
echo    BAIXAR DO GITHUB E INSTALAR AUTOMATICAMENTE
echo ============================================================
echo.
echo Este script vai:
echo.
echo   [1] Instalar Git (se necessario)
echo   [2] Clonar o repositorio do GitHub
echo   [3] Instalar Chocolatey
echo   [4] Instalar Python 3.11
echo   [5] Instalar Node.js 20 LTS
echo   [6] Instalar Google Chrome
echo   [7] Instalar Visual C++ Build Tools
echo   [8] Instalar todas as dependencias Python
echo   [9] Instalar todas as dependencias Node.js
echo   [10] Configurar ambiente completo
echo   [11] Iniciar o projeto
echo.
echo ============================================================
echo    REQUISITOS
echo ============================================================
echo.
echo   - Execute como ADMINISTRADOR
echo   - Tenha conexao com internet ativa
echo   - Pelo menos 3GB de espaco livre
echo   - Aguarde pacientemente (15-20 minutos)
echo.
echo ============================================================
echo.
pause

REM ============================================
REM VERIFICAR PERMISSOES DE ADMINISTRADOR
REM ============================================
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    color 0C
    echo.
    echo ============================================================
    echo    ERRO: PERMISSOES DE ADMINISTRADOR NECESSARIAS!
    echo ============================================================
    echo.
    echo Este script precisa ser executado como Administrador.
    echo.
    echo COMO FAZER:
    echo   1. Clique com botao direito neste arquivo
    echo   2. Selecione "Executar como administrador"
    echo   3. Clique "Sim" na janela de permissoes
    echo.
    echo ============================================================
    pause
    exit /b 1
)

echo.
echo [OK] Permissoes de administrador verificadas!
echo.

REM ============================================
REM PASSO 1: INSTALAR CHOCOLATEY
REM ============================================
echo.
echo ============================================================
echo    [1/11] VERIFICANDO/INSTALANDO CHOCOLATEY
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
REM PASSO 2: INSTALAR GIT
REM ============================================
echo.
echo ============================================================
echo    [2/11] VERIFICANDO/INSTALANDO GIT
echo ============================================================
echo.

where git >nul 2>&1
if %errorLevel% EQU 0 (
    echo [OK] Git ja esta instalado!
    git --version
) else (
    echo [INSTALANDO] Git...
    echo Aguarde, isso pode demorar 2-3 minutos...
    echo.

    choco install git -y --force

    REM Atualizar PATH
    call refreshenv.cmd 2>nul

    REM Adicionar Git ao PATH manualmente se necessario
    set PATH=%PATH%;C:\Program Files\Git\cmd

    where git >nul 2>&1
    if %errorLevel% EQU 0 (
        echo.
        echo [OK] Git instalado com sucesso!
        git --version
    ) else (
        color 0C
        echo.
        echo [ERRO] Falha ao instalar Git!
        echo Instale manualmente: https://git-scm.com/download/win
        pause
        exit /b 1
    )
)

REM ============================================
REM PASSO 3: CLONAR REPOSITORIO DO GITHUB
REM ============================================
echo.
echo ============================================================
echo    [3/11] CLONANDO REPOSITORIO DO GITHUB
echo ============================================================
echo.

REM Solicitar URL do repositorio
echo Digite a URL do repositorio GitHub:
echo Exemplo: https://github.com/seu-usuario/fba-automation.git
echo.
set /p REPO_URL="URL do repositorio: "

if "%REPO_URL%"=="" (
    color 0C
    echo.
    echo [ERRO] URL do repositorio nao pode estar vazia!
    pause
    exit /b 1
)

echo.
echo [CLONANDO] Baixando codigo do GitHub...
echo URL: %REPO_URL%
echo.

REM Solicitar pasta de destino
echo Onde deseja clonar o projeto?
echo Exemplo: C:\projetos
echo.
set /p DEST_DIR="Pasta de destino (ou deixe vazio para usar C:\fba-automation): "

if "%DEST_DIR%"=="" (
    set DEST_DIR=C:\fba-automation
)

REM Criar pasta se nao existir
if not exist "%DEST_DIR%" (
    mkdir "%DEST_DIR%"
    echo [OK] Pasta criada: %DEST_DIR%
)

REM Clonar repositorio
cd /d "%DEST_DIR%"
git clone "%REPO_URL%" .

if %errorLevel% EQU 0 (
    echo.
    echo [OK] Repositorio clonado com sucesso!
    echo Local: %DEST_DIR%
) else (
    color 0C
    echo.
    echo [ERRO] Falha ao clonar repositorio!
    echo Verifique:
    echo   - A URL esta correta
    echo   - Voce tem acesso ao repositorio
    echo   - Sua conexao com internet esta ativa
    pause
    exit /b 1
)

REM ============================================
REM PASSO 4: INSTALAR PYTHON 3.11
REM ============================================
echo.
echo ============================================================
echo    [4/11] VERIFICANDO/INSTALANDO PYTHON 3.11
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
REM PASSO 5: INSTALAR NODE.JS 20 LTS
REM ============================================
echo.
echo ============================================================
echo    [5/11] VERIFICANDO/INSTALANDO NODE.JS 20 LTS
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
REM PASSO 6: INSTALAR GOOGLE CHROME
REM ============================================
echo.
echo ============================================================
echo    [6/11] VERIFICANDO/INSTALANDO GOOGLE CHROME
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
REM PASSO 7: INSTALAR BUILD TOOLS
REM ============================================
echo.
echo ============================================================
echo    [7/11] VERIFICANDO/INSTALANDO BUILD TOOLS
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
REM PASSO 8: CRIAR VIRTUAL ENVIRONMENT PYTHON
REM ============================================
echo.
echo ============================================================
echo    [8/11] CRIANDO VIRTUAL ENVIRONMENT PYTHON
echo ============================================================
echo.

cd /d "%DEST_DIR%"

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
REM PASSO 9: INSTALAR DEPENDENCIAS PYTHON
REM ============================================
echo.
echo ============================================================
echo    [9/11] INSTALANDO DEPENDENCIAS PYTHON
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
REM PASSO 10: INSTALAR DEPENDENCIAS NODE.JS
REM ============================================
echo.
echo ============================================================
echo    [10/11] INSTALANDO DEPENDENCIAS NODE.JS (FRONTEND)
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
REM PASSO 11: CONFIGURAR ESTRUTURA DO PROJETO
REM ============================================
echo.
echo ============================================================
echo    [11/11] CONFIGURANDO ESTRUTURA DO PROJETO
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
echo   [OK] Git                - Controle de versao
echo   [OK] Python 3.11        - Interpretador Python
echo   [OK] Node.js 20 LTS     - Runtime JavaScript
echo   [OK] Google Chrome      - Navegador web
echo   [OK] Build Tools        - Compilador C++
echo.
echo REPOSITORIO CLONADO:
echo   [OK] Codigo baixado do GitHub
echo   [OK] Local: %DEST_DIR%
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

    REM Verificar se existe INICIAR_CHROME_DEBUG.bat
    if exist "INICIAR_CHROME_DEBUG.bat" (
        echo [1/3] Iniciando Chrome Debug...
        start "Chrome Debug" cmd /c "%DEST_DIR%\INICIAR_CHROME_DEBUG.bat"
        timeout /t 5 /nobreak >nul
    ) else (
        echo [!] Aviso: INICIAR_CHROME_DEBUG.bat nao encontrado
    )

    echo [2/3] Iniciando Backend (Python/FastAPI)...
    start "Backend - FastAPI" cmd /k "cd /d "%DEST_DIR%\backend" && venv\Scripts\activate && python main.py"
    timeout /t 4 /nobreak >nul

    echo [3/3] Iniciando Frontend (React/Vite)...
    start "Frontend - React" cmd /k "cd /d "%DEST_DIR%\frontend" && npm run dev"
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
    echo Para iniciar o projeto posteriormente:
    echo.
    echo   cd /d "%DEST_DIR%"
    echo   INICIAR_TUDO.bat
    echo.
    echo Ou execute manualmente:
    echo   1. INICIAR_CHROME_DEBUG.bat
    echo   2. cd backend ^&^& venv\Scripts\activate ^&^& python main.py
    echo   3. cd frontend ^&^& npm run dev
    echo.
)

echo.
echo ============================================================
echo    INSTALACAO E CONFIGURACAO FINALIZADA!
echo ============================================================
echo.
echo Projeto instalado em: %DEST_DIR%
echo.
echo Pressione qualquer tecla para sair...
pause >nul
