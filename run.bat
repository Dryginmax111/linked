@echo off
REM ============================================================
REM Запуск реестра на встроенном (embedded) Python 3.13.
REM Venv больше не нужен — все зависимости лежат в:
REM   runtime\embedded\python313\Lib\site-packages
REM ============================================================
cd /d "%~dp0"

set PYDIR=%~dp0runtime\embedded\python313
set EMBED_PY=%PYDIR%\python.exe

if not exist "%EMBED_PY%" (
    echo [ОШИБКА] Не найден embedded Python: "%EMBED_PY%"
    pause
    exit /b 1
)

REM Проверка, что библиотека Flask на месте
"%EMBED_PY%" -c "import flask, openpyxl, markupsafe" 1>nul 2>nul
if errorlevel 1 (
    echo [ОШИБКА] Зависимости не установлены. Запустите install_deps.bat
    pause
    exit /b 1
)

REM Project root (для импорта app.py и загрузки плагинов) + сайт-пакеты
set PYTHONPATH=%~dp0;%PYDIR%\Lib\site-packages

"%EMBED_PY%" run_embedded.py %*
pause
