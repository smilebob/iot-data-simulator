@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

REM ============================================================================
REM IoT Data Simulator - Lanceur Portable Windows (0 droit administrateur)
REM Plan B universel lorsque l'EDR bloque les executables non signes.
REM ============================================================================

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"
cd /d "%PROJECT_ROOT%"

set "IOT_SIM_PORTABLE=1"
set "USER_ENV_DIR=%LOCALAPPDATA%\IoT-Data-Simulator"
set "VENV_DIR=%USER_ENV_DIR%\venv"
set "UV_BIN=%USER_ENV_DIR%\bin\uv.exe"

echo ================================================================
echo   IoT Data Simulator - Mode Portable Windows (Sans Droits Admin)
echo ================================================================
echo.

REM 1. Utiliser uv si deja present dans le PATH
where uv >nul 2>&1
if %ERRORLEVEL%==0 (
    echo [INFO] Lanceur rapide 'uv' detecte. Demarrage du simulateur...
    uv run --with-requirements "%PROJECT_ROOT%\requirements.txt" python "%PROJECT_ROOT%\launcher.py" %*
    goto :end
)

REM 2. Utiliser uv portable deja telecharge dans %LOCALAPPDATA%
if exist "%UV_BIN%" (
    echo [INFO] Lanceur portable 'uv' detecte dans %USER_ENV_DIR%. Demarrage...
    "%UV_BIN%" run --with-requirements "%PROJECT_ROOT%\requirements.txt" python "%PROJECT_ROOT%\launcher.py" %*
    goto :end
)

REM 3. Utiliser Python (py ou python) si disponible en espace utilisateur
set "PY_CMD="
where py >nul 2>&1 && set "PY_CMD=py -3"
if "%PY_CMD%"=="" (
    where python >nul 2>&1 && set "PY_CMD=python"
)

if not "%PY_CMD%"=="" (
    if not exist "%VENV_DIR%\Scripts\python.exe" (
        echo [INFO] Creation de l'environnement virtuel isole dans %VENV_DIR%...
        if not exist "%USER_ENV_DIR%" mkdir "%USER_ENV_DIR%"
        %PY_CMD% -m venv "%VENV_DIR%"
        if errorlevel 1 (
            echo [ERREUR] Impossible de creer l'environnement virtuel Python.
            pause
            exit /b 1
        )
        echo [INFO] Installation des dependances Python (1ere execution uniquement)...
        "%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip --quiet
        "%VENV_DIR%\Scripts\pip.exe" install -r "%PROJECT_ROOT%\requirements.txt"
    )
    "%VENV_DIR%\Scripts\python.exe" "%PROJECT_ROOT%\launcher.py" %*
    goto :end
)

REM 4. Ni uv ni Python trouves -> telechargement user-space de uv (aucun droit admin)
echo [INFO] Aucun Python ou uv detecte. Installation portable de 'uv' dans %USER_ENV_DIR%...
if not exist "%USER_ENV_DIR%\bin" mkdir "%USER_ENV_DIR%\bin"
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
if exist "%USERPROFILE%\.local\bin\uv.exe" (
    "%USERPROFILE%\.local\bin\uv.exe" run --with-requirements "%PROJECT_ROOT%\requirements.txt" python "%PROJECT_ROOT%\launcher.py" %*
    goto :end
)

echo [ERREUR] Impossible d'initialiser Python/uv automatiquement (proxy ou hors-ligne).
echo          Utilisez la version binaire autonome IoT-Data-Simulator-Windows-x64.zip depuis GitHub Releases.
pause
exit /b 1

:end
if %ERRORLEVEL% NEQ 0 pause
