@echo off
setlocal enabledelayedexpansion
title Evo Chatterbox - Setup
cd /d "%~dp0"
chcp 65001 >nul 2>nul

echo.
echo ==========================================
echo   Evo Chatterbox - First Time Setup
echo ==========================================
echo.
echo   This will install everything you need.
echo   It may take a few minutes.
echo   Do not close this window.
echo.

:: ------------------------------------------
::  Detect Python
:: ------------------------------------------
set "BOOTSTRAP_PYTHON="
set "USE_VENV=1"

:: Check for portable python folder
if exist "%~dp0python\python.exe" (
    :: Check if this is an embeddable install (has ._pth file, no venv support)
    if exist "%~dp0python\python*._pth" (
        set "BOOTSTRAP_PYTHON=%~dp0python\python.exe"
        set "USE_VENV=0"
    ) else (
        set "BOOTSTRAP_PYTHON=%~dp0python\python.exe"
    )
)
if not defined BOOTSTRAP_PYTHON if exist "%~dp0runtime\python.exe" set "BOOTSTRAP_PYTHON=%~dp0runtime\python.exe"
if not defined BOOTSTRAP_PYTHON (
    where python >nul 2>nul
    if errorlevel 1 goto :auto_install_python
    set "BOOTSTRAP_PYTHON=python"
)

echo   Python found: %BOOTSTRAP_PYTHON%
echo.
goto :setup_env

:: ------------------------------------------
::  Auto-install Python Embeddable
:: ------------------------------------------
:auto_install_python
echo   Python not found. Downloading portable version...
echo.

set "PY_VER=3.11.9"
set "PY_ZIP=python-%PY_VER%-embed-amd64.zip"
set "PY_URL=https://www.python.org/ftp/python/%PY_VER%/%PY_ZIP%"
set "PIP_URL=https://bootstrap.pypa.io/get-pip.py"
set "PY_DIR=%~dp0python"

:: Download embeddable zip
echo   [1/3] Downloading Python %PY_VER% (~11 MB)...
curl.exe -L --fail --progress-bar -o "%~dp0%PY_ZIP%" "%PY_URL%"
if errorlevel 1 goto :fail_python_download
if not exist "%~dp0%PY_ZIP%" goto :fail_python_download

:: Extract
echo   [2/3] Extracting Python...
if exist "%PY_DIR%" rmdir /s /q "%PY_DIR%"
mkdir "%PY_DIR%"
powershell -NoProfile -Command "Expand-Archive -Path '%~dp0%PY_ZIP%' -DestinationPath '%PY_DIR%' -Force"
if errorlevel 1 goto :fail_python_extract
del "%~dp0%PY_ZIP%" 2>nul

if not exist "%PY_DIR%\python.exe" goto :fail_python_extract

:: Enable site-packages by uncommenting "import site" in ._pth file
for %%f in ("%PY_DIR%\python*._pth") do (
    powershell -NoProfile -Command "(Get-Content '%%f') -replace '^#import site','import site' | Set-Content '%%f'"
)

:: Install pip
echo   [3/3] Installing pip...
curl.exe -L --fail --silent -o "%PY_DIR%\get-pip.py" "%PIP_URL%"
if errorlevel 1 goto :fail_pip
"%PY_DIR%\python.exe" "%PY_DIR%\get-pip.py" --no-warn-script-location >nul 2>nul
if errorlevel 1 goto :fail_pip
del "%PY_DIR%\get-pip.py" 2>nul

set "BOOTSTRAP_PYTHON=%PY_DIR%\python.exe"
set "USE_VENV=0"
echo.
echo   Python %PY_VER% portable installed!
echo.

:: ------------------------------------------
::  Setup environment
:: ------------------------------------------
:setup_env

:: Create local cache directories
if not exist ".cache\huggingface\hub" mkdir ".cache\huggingface\hub"
if not exist ".cache\pkuseg" mkdir ".cache\pkuseg"
if not exist "output" mkdir "output"

set "HF_HOME=%cd%\.cache\huggingface"
set "HUGGINGFACE_HUB_CACHE=%cd%\.cache\huggingface\hub"
set "PKUSEG_HOME=%cd%\.cache\pkuseg"
set "HF_HUB_DISABLE_SYMLINKS_WARNING=1"

:: ------------------------------------------
::  Determine which Python to use for packages
:: ------------------------------------------
if "%USE_VENV%"=="0" (
    set "APP_PYTHON=%BOOTSTRAP_PYTHON%"
    echo [1/4] Using portable Python directly...
    echo       No virtual environment needed.
) else (
    echo [1/4] Creating Python environment...
    if not exist ".venv\Scripts\python.exe" (
        "%BOOTSTRAP_PYTHON%" -m venv .venv
        if errorlevel 1 goto :fail_install
        echo       Done.
    ) else (
        echo       Already exists.
    )
    set "APP_PYTHON=%cd%\.venv\Scripts\python.exe"
)
echo.

:: ------------------------------------------
::  Step 2: Install dependencies
:: ------------------------------------------
echo [2/4] Installing dependencies...
echo       This may take a while on first run.
"%APP_PYTHON%" -m pip install --upgrade pip >nul 2>nul
"%APP_PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 goto :fail_install
echo       Done.
echo.

:: ------------------------------------------
::  Step 3: Detect GPU
:: ------------------------------------------
echo [3/4] Checking for NVIDIA GPU...
where nvidia-smi >nul 2>nul
if errorlevel 1 (
    echo       No NVIDIA GPU detected. Using CPU mode.
    echo       [This is normal if you don't have a dedicated graphics card]
    echo.
    goto :install_done
)

echo       NVIDIA GPU detected!
"%APP_PYTHON%" -c "import torch; exit(0 if '+cu' in torch.__version__ and torch.cuda.is_available() else 1)" >nul 2>nul
if not errorlevel 1 (
    echo       GPU acceleration already active.
    echo.
    goto :install_done
)

echo       Installing GPU acceleration (CUDA)...
echo       This download is large and may take several minutes.
"%APP_PYTHON%" -m pip install --force-reinstall torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124
if errorlevel 1 goto :fail_install
"%APP_PYTHON%" -m pip install --force-reinstall "numpy<2"
if errorlevel 1 goto :fail_install
echo       GPU acceleration installed!
echo.

:: ------------------------------------------
::  Step 4: Save install marker
:: ------------------------------------------
:install_done
echo [4/4] Finishing setup...

:: Save marker with mode info so start.bat knows which python to use
if "%USE_VENV%"=="0" (
    echo embed> ".installed"
) else (
    echo venv> ".installed"
)

echo.
echo ==========================================
echo   Setup complete!
echo ==========================================
echo.
echo   You can now run start.bat to launch
echo   the application.
echo.
echo ==========================================
pause
exit /b 0

:: ==========================================
::   Error Messages
:: ==========================================
:fail_python_download
del "%~dp0%PY_ZIP%" 2>nul
echo.
echo ==========================================
echo   Could not download Python!
echo ==========================================
echo.
echo   Check your internet connection and
echo   try running install.bat again.
echo.
echo ==========================================
pause
exit /b 1

:fail_python_extract
del "%~dp0%PY_ZIP%" 2>nul
echo.
echo ==========================================
echo   Could not extract Python!
echo ==========================================
echo.
echo   Make sure you have enough disk space
echo   and try running install.bat again.
echo.
echo ==========================================
pause
exit /b 1

:fail_pip
echo.
echo ==========================================
echo   Could not install pip!
echo ==========================================
echo.
echo   Check your internet connection and
echo   try running install.bat again.
echo.
echo ==========================================
pause
exit /b 1

:fail_install
echo.
echo ==========================================
echo   Installation failed!
echo ==========================================
echo.
echo   Possible causes:
echo   - No internet connection
echo   - Antivirus blocking the download
echo   - Not enough disk space
echo.
echo   Try:
echo   1. Check your internet connection
echo   2. Temporarily disable your antivirus
echo   3. Run install.bat again
echo.
echo   If the error persists, delete the
echo   ".venv" folder (or "python" folder)
echo   and try again.
echo.
echo ==========================================
pause
exit /b 1
