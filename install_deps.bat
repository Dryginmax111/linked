@echo off
REM ============================================================
REM Установка зависимостей В ВНУТРЬ embedded Python
REM (runtime\embedded\python313\Lib\site-packages).
REM Работает без venv: pip вызывается как модуль, target = site-packages.
REM ============================================================
cd /d "%~dp0"

set PYDIR=%~dp0runtime\embedded\python313
set EMBED_PY=%PYDIR%\python.exe
set SITE=%PYDIR%\Lib\site-packages

if not exist "%EMBED_PY%" (
    echo [ОШИБКА] Не найден embedded Python: "%EMBED_PY%"
    pause
    exit /b 1
)

if not exist "%SITE%" mkdir "%SITE%"

echo [1/2] Основные зависимости (requirements.txt)...
"%EMBED_PY%" -m pip install --no-warn-script-location --target "%SITE%" -r requirements.txt
if errorlevel 1 (
    echo [ОШИБКА] Не удалось установить зависимости.
    pause
    exit /b 1
)

echo [2/2] Зависимости плагинов (plugins_requirements.txt)...
if exist plugins_requirements.txt (
    for %%F in (plugins_requirements.txt) do if not %%~zF==0 (
        "%EMBED_PY%" -m pip install --no-warn-script-location --target "%SITE%" -r plugins_requirements.txt
    )
)

echo.
echo Готово. Запуск: run.bat
pause
