@echo off
REM ============================================
REM ATALHO RAPIDO - INSTALADOR COMPLETO
REM Duplo clique para instalar TUDO!
REM ============================================

color 0E
title Instalador Rapido - FBA Automation

echo.
echo ============================================================
echo    BEM-VINDO AO INSTALADOR FBA AUTOMATION
echo ============================================================
echo.
echo Este script vai:
echo   - Verificar se voce tem permissoes de Administrador
echo   - Instalar TUDO automaticamente (Python, Node, Chrome, etc)
echo   - Configurar o projeto completo
echo   - Iniciar o sistema
echo.
echo Tempo estimado: 10-15 minutos
echo.
echo ============================================================
echo.

REM Verificar se esta rodando como Admin
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo.
    echo ============================================================
    echo    PERMISSOES DE ADMINISTRADOR NECESSARIAS
    echo ============================================================
    echo.
    echo Este instalador precisa de permissoes de Administrador.
    echo.
    echo REDIRECIONANDO...
    echo Aguarde, uma nova janela vai abrir solicitando permissoes.
    echo.
    timeout /t 3 /nobreak >nul

    REM Reiniciar como Admin
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b 0
)

echo [OK] Permissoes verificadas! Iniciando instalacao...
echo.
timeout /t 2 /nobreak >nul

REM Executar instalador completo
call "%~dp0INSTALAR_E_INICIAR_COMPLETO.bat"

echo.
echo Instalacao finalizada!
pause
