@echo off
REM Start AJAX Local - Web Edition
echo.
echo ========================================
echo   AJAX Super-Agent - Inicializando
echo ========================================
echo   Modelo: qwen2.5-coder:1.5b (Ollama)
echo   Capacidades: Fullstack, Mobile, Web
echo ========================================
echo.

REM Verificar e baixar modelo se necessario
echo Verificando modelo qwen2.5-coder:1.5b...
ollama list 2>nul | findstr "qwen2.5-coder:1.5b" >nul
if errorlevel 1 (
    echo Modelo nao encontrado. Baixando qwen2.5-coder:1.5b (~986MB)...
    ollama pull qwen2.5-coder:1.5b
    echo.
)

REM Backend (FastAPI)
echo Iniciando Backend...
start "AJAX Backend" cmd /k "cd /d %~dp0app\backend && python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3

REM Frontend (React)
echo Iniciando Frontend...
start "AJAX Frontend" cmd /k "cd /d %~dp0app\frontend && yarn start"

echo.
echo Tudo iniciado! Aguarde alguns segundos para que todos os servicos estejam prontos:
echo   Backend: http://localhost:8000
echo   Frontend: http://localhost:3000
echo   Modelo: qwen2.5-coder:1.5b (Ollama local)
echo.

REM Espera mais 15 segundos para mostrar o link correto ao usuario
timeout /t 15 >nul

echo.
echo Aguarde ~15s e abra: http://localhost:3000
echo.
pause

