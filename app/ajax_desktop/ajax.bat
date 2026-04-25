@echo off
REM Lança o Ajax Desktop usando o Python do sistema.
REM Coloca este .bat na mesma pasta do projeto Ajax.
cd /d "%~dp0\.."
py ajax_desktop\desktop_app.py %*
pause
