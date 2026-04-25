@echo off
REM Initialize RAG Database
echo.
echo ========================================
echo   Inicializando RAG Database
echo ========================================
echo.
echo Isto vai popular a base de conhecimento do RAG
echo com materiais de Python, Java, C, C++, C#, Go
echo.
pause

cd /d %~dp0

if not exist "app\backend" (
    echo ERRO: Pasta app\backend nao encontrada
    pause
    exit /b 1
)

cd app\backend
echo Executando seed_rag.py...
python seed_rag.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ RAG inicializado com sucesso!
    echo.
) else (
    echo.
    echo ❌ Erro ao inicializar RAG
    echo.
)

pause
