@echo off
REM ============================================
REM INICIAR TUDO - FBA AUTOMATION
REM Windows - Duplo Clique para Iniciar
REM ============================================

color 0B
title Iniciar FBA Automation

echo.
echo ==========================================
echo    INICIANDO FBA AUTOMATION COMPLETO
echo ==========================================
echo.

REM Obter diretorio do script
set PROJECT_DIR=%~dp0
cd /d "%PROJECT_DIR%"

REM Criar pasta de logs
if not exist "logs" mkdir logs

echo [1/3] Iniciando Chrome Debug...
start "Chrome Debug" cmd /c "%PROJECT_DIR%INICIAR_CHROME_DEBUG.bat"

timeout /t 5 /nobreak >nul

echo.
echo [2/3] Iniciando Backend...
start "Backend - FastAPI" cmd /k "cd /d "%PROJECT_DIR%backend" && venv\Scripts\activate && python main.py"

timeout /t 4 /nobreak >nul

echo.
echo [3/3] Iniciando Frontend...
start "Frontend - React" cmd /k "cd /d "%PROJECT_DIR%frontend" && npm run dev"

timeout /t 4 /nobreak >nul

echo.
echo ==========================================
echo    SISTEMA INICIADO COM SUCESSO!
echo ==========================================
echo.
echo Servicos rodando em 3 janelas separadas:
echo.
echo   [1] Chrome Debug     - porta 9222
echo   [2] Backend (Python) - porta 8001
echo   [3] Frontend (React) - porta 5173
echo.
echo ==========================================
echo    ACESSE O SISTEMA
echo ==========================================
echo.
echo   Frontend:     http://localhost:5173
echo   Backend API:  http://localhost:8001
echo   Docs API:     http://localhost:8001/docs
echo.
echo ==========================================
echo    COMO USAR
echo ==========================================
echo.
echo 1. Use o Chrome DEBUG (janela roxa) para abrir produtos
echo 2. Acesse http://localhost:5173/capture no seu navegador
echo 3. Clique em "Capturar Abas"
echo 4. Os produtos serao extraidos automaticamente
echo.
echo IMPORTANTE: Nao feche as 3 janelas que abriram!
echo            (Chrome Debug, Backend, Frontend)
echo.
echo Pressione qualquer tecla para abrir o navegador...
pause >nul

REM Aguardar um pouco mais para garantir que tudo iniciou
timeout /t 2 /nobreak >nul

REM Abrir navegador
start http://localhost:5173

echo.
echo Sistema aberto no navegador!
echo.
echo Para PARAR o sistema:
echo   - Feche as 3 janelas (Chrome Debug, Backend, Frontend)
echo.
echo Pressione qualquer tecla para fechar esta janela...
pause >nul
