@echo off
REM Setup AJAX Local com qwen2.5-coder:1.5b
chcp 65001 >nul
echo.
echo ========================================
echo   AJAX Super-Agent - Setup qwen2.5-coder:1.5b
echo ========================================
echo.

REM 1. Verificar Ollama
echo [1/4] Verificando Ollama...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Ollama não encontrado. Instale em https://ollama.com/download
    pause
    exit /b 1
)
echo ✅ Ollama encontrado

REM 2. Iniciar Ollama se necessario
echo [2/4] Iniciando Ollama...
tasklist | findstr "ollama" >nul
if errorlevel 1 (
    start "Ollama" cmd /k "ollama serve"
    timeout /t 5 >nul
)
echo ✅ Ollama rodando

REM 3. Baixar modelo
echo [3/4] Baixando qwen2.5-coder:1.5b (~986MB)...
ollama pull qwen2.5-coder:1.5b
if errorlevel 1 (
    echo ❌ Falha ao baixar modelo
    pause
    exit /b 1
)
echo ✅ Modelo qwen2.5-coder:1.5b instalado

REM 4. Atualizar RAG
echo [4/4] Populando base de conhecimento (RAG)...
cd /d %~dp0app\backend
call venv_backend\Scripts\python.exe seed_rag.py
echo ✅ RAG atualizado

echo.
echo ========================================
echo   ✅ Setup completo!
echo ========================================
echo.
echo Pronto para rodar. Execute:
echo   START.bat   (Web App)
echo   START_DESKTOP.bat   (Desktop App)
echo.
pause
