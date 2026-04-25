@echo off
REM Clean and reinstall frontend dependencies
echo.
echo ========================================
echo   Limpando Frontend
echo ========================================
echo.

cd /d %~dp0\app\frontend

echo Removendo node_modules...
rmdir /s /q node_modules 2>nul
del yarn.lock 2>nul
del package-lock.json 2>nul

echo.
echo Reinstalando dependências...
yarn install

echo.
echo ✅ Frontend limpo e reinstalado!
echo.
pause
