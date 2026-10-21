@echo off
setlocal EnableExtensions
cd /d "%~dp0"

REM ============================================================
REM Registry launcher on embedded Python 3.13.
REM If libs are missing - install them once from local wheels.
REM ============================================================

set "PYDIR=%~dp0runtime\embedded\python313"
set "EMBED_PY=%PYDIR%\python.exe"
set "SITE=%PYDIR%\Lib\site-packages"

set "UNZIP_SCRIPT=%~dp0tools\unzip_wheels.py"
if not exist "%UNZIP_SCRIPT%" set "UNZIP_SCRIPT=%~dp0unzip_wheels.py"

set "WHEELS_DIR=%~dp0tools\wheels"
if not exist "%WHEELS_DIR%" set "WHEELS_DIR=%~dp0wheels"

if not exist "%EMBED_PY%" goto :no_python

"%EMBED_PY%" -c "import flask, openpyxl, markupsafe" 1>nul 2>nul
if not errorlevel 1 goto :run

echo.
echo [INFO] Dependencies not found. Installing from local wheels...
echo.

if not exist "%WHEELS_DIR%" goto :no_wheels
if not exist "%UNZIP_SCRIPT%" goto :no_unzip

if not exist "%SITE%" mkdir "%SITE%"

echo Unpacking wheels:
echo   from: "%WHEELS_DIR%"
echo   into: "%SITE%"
echo.

"%EMBED_PY%" "%UNZIP_SCRIPT%" "%WHEELS_DIR%" "%SITE%"
if errorlevel 1 goto :unzip_failed

"%EMBED_PY%" -c "import flask, openpyxl, markupsafe" 1>nul 2>nul
if errorlevel 1 goto :still_broken

echo.
echo [OK] Dependencies installed from local wheels.
echo.

:run
set "PYTHONPATH=%~dp0;%SITE%"
"%EMBED_PY%" run_embedded.py %*
pause
exit /b 0

:no_python
echo [ERROR] Embedded Python not found: "%EMBED_PY%"
echo Unpack python-3.13.x-embed-amd64.zip
echo into runtime\embedded\python313
pause
exit /b 1

:no_wheels
echo [ERROR] Wheels directory not found.
echo Looked in: "%~dp0tools\wheels" and "%~dp0wheels"
echo Put .whl files there or run install_deps.bat (needs internet).
pause
exit /b 1

:no_unzip
echo [ERROR] unzip_wheels.py not found.
echo Looked in: "%~dp0tools\unzip_wheels.py" and "%~dp0unzip_wheels.py"
pause
exit /b 1

:unzip_failed
echo.
echo [ERROR] Failed to unpack wheels.
echo Check that .whl files match Python 3.13
echo (tags cp313-cp313-win_amd64 or py3-none-any).
pause
exit /b 1

:still_broken
echo.
echo [ERROR] Import still fails after unpacking wheels.
echo Probably some dependencies are missing:
echo   Flask    needs: werkzeug, jinja2, itsdangerous, click, blinker, markupsafe
echo   openpyxl needs: et-xmlfile
pause
exit /b 1