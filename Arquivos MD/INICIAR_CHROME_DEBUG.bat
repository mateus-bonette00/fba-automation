@echo off
REM ============================================
REM INICIAR CHROME DEBUG - FBA AUTOMATION
REM Windows - Duplo Clique para Iniciar
REM ============================================

color 0D
title Chrome Debug - Porta 9222

echo.
echo ==========================================
echo    INICIANDO CHROME DEBUG
echo ==========================================
echo.

REM Matar processos na porta 9222
echo [1/4] Liberando porta 9222...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":9222" ^| find "LISTENING"') do (
    echo Matando processo PID %%a...
    taskkill /F /PID %%a 2>nul
)

timeout /t 2 /nobreak >nul

REM Matar processos Chrome que podem estar travados
echo.
echo [2/4] Fechando Chrome antigo...
taskkill /F /IM chrome.exe 2>nul
timeout /t 2 /nobreak >nul

REM Encontrar caminho do Chrome
echo.
echo [3/4] Procurando Google Chrome...

set CHROME_PATH=
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe
    echo [OK] Chrome encontrado em: Program Files
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe
    echo [OK] Chrome encontrado em: Program Files (x86)
) else (
    echo.
    echo ==========================================
    echo ERRO: Google Chrome nao encontrado!
    echo ==========================================
    echo.
    echo Por favor, instale o Google Chrome em:
    echo https://www.google.com/chrome/
    echo.
    echo Ou execute: INSTALAR_WINDOWS.bat
    echo.
    pause
    exit /b 1
)

REM Criar pasta temporaria
if not exist "%TEMP%\chrome-debug-profile" mkdir "%TEMP%\chrome-debug-profile"

REM Criar página HTML de boas-vindas
echo ^<!DOCTYPE html^> > "%TEMP%\chrome-debug-start.html"
echo ^<html^> >> "%TEMP%\chrome-debug-start.html"
echo ^<head^> >> "%TEMP%\chrome-debug-start.html"
echo ^<title^>CHROME DEBUG - ABRA SEUS PRODUTOS AQUI!^</title^> >> "%TEMP%\chrome-debug-start.html"
echo ^<style^> >> "%TEMP%\chrome-debug-start.html"
echo body{margin:0;padding:40px;font-family:Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%%,#764ba2 100%%);color:white;text-align:center;min-height:100vh;display:flex;align-items:center;justify-content:center} >> "%TEMP%\chrome-debug-start.html"
echo .container{max-width:700px} >> "%TEMP%\chrome-debug-start.html"
echo h1{font-size:48px;margin-bottom:20px;text-shadow:2px 2px 4px rgba(0,0,0,0.3)} >> "%TEMP%\chrome-debug-start.html"
echo .badge{background:rgba(255,255,255,0.2);padding:15px 30px;border-radius:50px;font-size:20px;font-weight:bold;margin:20px 0;display:inline-block} >> "%TEMP%\chrome-debug-start.html"
echo .instructions{background:rgba(0,0,0,0.2);padding:30px;border-radius:15px;margin-top:30px;text-align:left} >> "%TEMP%\chrome-debug-start.html"
echo .step{margin:15px 0;font-size:18px} >> "%TEMP%\chrome-debug-start.html"
echo .warning{background:rgba(255,193,7,0.3);padding:20px;border-radius:10px;margin-top:20px;border-left:5px solid #ffc107} >> "%TEMP%\chrome-debug-start.html"
echo ^</style^> >> "%TEMP%\chrome-debug-start.html"
echo ^</head^> >> "%TEMP%\chrome-debug-start.html"
echo ^<body^> >> "%TEMP%\chrome-debug-start.html"
echo ^<div class="container"^> >> "%TEMP%\chrome-debug-start.html"
echo ^<h1^>CHROME DEBUG^</h1^> >> "%TEMP%\chrome-debug-start.html"
echo ^<div class="badge"^>Conectado na porta 9222^</div^> >> "%TEMP%\chrome-debug-start.html"
echo ^<div class="instructions"^> >> "%TEMP%\chrome-debug-start.html"
echo ^<h2^>Como usar:^</h2^> >> "%TEMP%\chrome-debug-start.html"
echo ^<div class="step"^>1. Abra NOVAS ABAS neste Chrome (Ctrl+T)^</div^> >> "%TEMP%\chrome-debug-start.html"
echo ^<div class="step"^>2. Cole as URLs dos produtos^</div^> >> "%TEMP%\chrome-debug-start.html"
echo ^<div class="step"^>3. Volte para http://localhost:5173/capture^</div^> >> "%TEMP%\chrome-debug-start.html"
echo ^<div class="step"^>4. Clique em "Capturar Abas"^</div^> >> "%TEMP%\chrome-debug-start.html"
echo ^</div^> >> "%TEMP%\chrome-debug-start.html"
echo ^<div class="warning"^> >> "%TEMP%\chrome-debug-start.html"
echo ^<strong^>IMPORTANTE:^</strong^>^<br^> >> "%TEMP%\chrome-debug-start.html"
echo Use APENAS este Chrome!^<br^> >> "%TEMP%\chrome-debug-start.html"
echo Se usar outro, a captura nao funciona. >> "%TEMP%\chrome-debug-start.html"
echo ^</div^> >> "%TEMP%\chrome-debug-start.html"
echo ^</div^> >> "%TEMP%\chrome-debug-start.html"
echo ^</body^> >> "%TEMP%\chrome-debug-start.html"
echo ^</html^> >> "%TEMP%\chrome-debug-start.html"

echo.
echo [4/4] Iniciando Chrome na porta 9222...
echo.
echo ==========================================
echo    CHROME DEBUG INICIADO!
echo ==========================================
echo.
echo Uma nova janela do Chrome vai abrir com:
echo   - Fundo ROXO
echo   - Titulo: "CHROME DEBUG - ABRA SEUS PRODUTOS AQUI!"
echo.
echo IMPORTANTE:
echo   Use ESTE Chrome para abrir os produtos!
echo   Nao use seu Chrome normal!
echo.
echo Porta: 9222
echo Status: Rodando
echo.
echo Pressione qualquer tecla para continuar...
pause >nul

REM Iniciar Chrome
start "" "%CHROME_PATH%" ^
    --remote-debugging-port=9222 ^
    --user-data-dir="%TEMP%\chrome-debug-profile" ^
    --disable-extensions ^
    --no-first-run ^
    --no-default-browser-check ^
    "file:///%TEMP%\chrome-debug-start.html"

echo.
echo Chrome Debug iniciado!
echo.
echo Esta janela pode ser fechada.
echo O Chrome continuara rodando.
echo.
timeout /t 5 /nobreak
