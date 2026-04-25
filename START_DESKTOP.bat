@echo off
REM Start AJAX Local - Desktop Edition
echo.
echo ========================================
echo   AJAX Super-Agent - Desktop Setup
echo ========================================
echo.
echo Este script vai abrir 2 janelas:
echo   1. Ollama (LLM + embeddings)
echo   2. Desktop App (CustomTkinter)
echo.
pause

cd /d %~dp0

REM Check if folders exist
if not exist "app\ajax_desktop" (
    echo ERRO: Pasta app\ajax_desktop nao encontrada
    pause
    exit /b 1
)

REM Terminal 1: Ollama
echo Iniciando Ollama...
start "Ollama" cmd /k "ollama serve"
timeout /t 3

REM Terminal 2: Desktop App
echo Iniciando Desktop App...
start "Desktop App" cmd /k "cd /d %~dp0app\ajax_desktop && python desktop_app.py"

echo.
echo Tudo iniciado!
echo.
pause
