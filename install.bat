@echo off
setlocal enabledelayedexpansion
title Evo Chatterbox - Setup
cd /d "%~dp0"
chcp 65001 >nul 2>nul

set "BOOTSTRAP_PYTHON="
set "APP_PYTHON="
set "USE_VENV=1"
set "PY_VER=3.11.9"
set "PY_ZIP=python-%PY_VER%-embed-amd64.zip"
set "PY_URL=https://www.python.org/ftp/python/%PY_VER%/%PY_ZIP%"
set "PIP_URL=https://bootstrap.pypa.io/get-pip.py"
set "PY_DIR=%~dp0python"

echo.
echo ==========================================
echo   Evo Chatterbox - First Time Setup
echo ==========================================
echo.
echo   This installer checks each requirement
echo   step by step and only installs what is
echo   missing on this computer.
echo.

echo [1/6] Checking system requirements...
call :preflight_checks
if errorlevel 1 exit /b 1
echo       OK. Folder, PowerShell, and disk space look good.
echo.

echo [2/6] Checking Python...
call :ensure_python
if errorlevel 1 exit /b 1
echo.

echo [3/6] Preparing app folders...
call :prepare_runtime_dirs
if errorlevel 1 exit /b 1
echo       Runtime folders ready.
echo.

echo [4/6] Checking Python environment...
call :prepare_python_environment
if errorlevel 1 exit /b 1
echo.

echo [5/6] Checking Python packages...
call :install_dependencies
if errorlevel 1 exit /b 1
echo.

echo [6/6] Checking GPU acceleration...
call :ensure_gpu_acceleration
if errorlevel 1 exit /b 1
echo.

echo Finishing setup...
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

:ensure_python
if exist "%~dp0python\python.exe" (
    call :validate_python_command "%~dp0python\python.exe"
    if not errorlevel 1 (
        if exist "%~dp0python\python*._pth" (
            set "USE_VENV=0"
        )
        echo       Python found: !BOOTSTRAP_PYTHON!
        exit /b 0
    )
)

if exist "%~dp0runtime\python.exe" (
    call :validate_python_command "%~dp0runtime\python.exe"
    if not errorlevel 1 (
        echo       Python found: !BOOTSTRAP_PYTHON!
        exit /b 0
    )
)

where python >nul 2>nul
if not errorlevel 1 (
    call :validate_python_command python
    if not errorlevel 1 (
        echo       Python found: !BOOTSTRAP_PYTHON!
        exit /b 0
    )
    echo       Ignoring invalid Python command from PATH.
)

goto :auto_install_python

:auto_install_python
echo       Python not found.
echo       Downloading portable Python automatically...
call :download_file "%PY_URL%" "%~dp0%PY_ZIP%"
if errorlevel 1 goto :fail_python_download
if not exist "%~dp0%PY_ZIP%" goto :fail_python_download

echo       Extracting Python...
if exist "%PY_DIR%" rmdir /s /q "%PY_DIR%"
mkdir "%PY_DIR%"
powershell -NoProfile -Command "Expand-Archive -Path '%~dp0%PY_ZIP%' -DestinationPath '%PY_DIR%' -Force"
if errorlevel 1 goto :fail_python_extract
del "%~dp0%PY_ZIP%" 2>nul

if not exist "%PY_DIR%\python.exe" goto :fail_python_extract

for %%f in ("%PY_DIR%\python*._pth") do (
    powershell -NoProfile -Command "(Get-Content '%%f') -replace '^#import site','import site' | Set-Content '%%f'"
)

echo       Installing pip for portable Python...
call :download_file "%PIP_URL%" "%PY_DIR%\get-pip.py"
if errorlevel 1 goto :fail_pip
"%PY_DIR%\python.exe" "%PY_DIR%\get-pip.py" --no-warn-script-location >nul 2>nul
if errorlevel 1 goto :fail_pip
del "%PY_DIR%\get-pip.py" 2>nul

set "BOOTSTRAP_PYTHON=%PY_DIR%\python.exe"
set "USE_VENV=0"
echo       Python %PY_VER% portable installed.
exit /b 0

:validate_python_command
set "BOOTSTRAP_PYTHON="
%~1 -c "import sys" >nul 2>nul
if errorlevel 1 exit /b 1
set "BOOTSTRAP_PYTHON=%~1"
exit /b 0

:prepare_runtime_dirs
if not exist ".cache\huggingface\hub" mkdir ".cache\huggingface\hub"
if not exist ".cache\pkuseg" mkdir ".cache\pkuseg"
if not exist "output" mkdir "output"

set "HF_HOME=%cd%\.cache\huggingface"
set "HUGGINGFACE_HUB_CACHE=%cd%\.cache\huggingface\hub"
set "PKUSEG_HOME=%cd%\.cache\pkuseg"
set "HF_HUB_DISABLE_SYMLINKS_WARNING=1"
exit /b 0

:prepare_python_environment
if "%USE_VENV%"=="0" (
    set "APP_PYTHON=%BOOTSTRAP_PYTHON%"
    echo       Using portable Python directly.
    call :ensure_pip "%APP_PYTHON%"
    if errorlevel 1 goto :fail_pip
    exit /b 0
)

if not exist ".venv\Scripts\python.exe" (
    echo       Creating local Python environment...
    "%BOOTSTRAP_PYTHON%" -m venv .venv
    if errorlevel 1 goto :fail_install
    echo       Python environment created.
) else (
    echo       Local Python environment already exists.
)

set "APP_PYTHON=%cd%\.venv\Scripts\python.exe"
call :ensure_pip "%APP_PYTHON%"
if errorlevel 1 goto :fail_pip
echo       Python environment ready.
exit /b 0

:ensure_pip
set "TARGET_PYTHON=%~1"
"%TARGET_PYTHON%" -m pip --version >nul 2>nul
if not errorlevel 1 (
    echo       pip already available.
    exit /b 0
)

echo       pip not found. Installing pip...
"%TARGET_PYTHON%" -m ensurepip --upgrade >nul 2>nul
"%TARGET_PYTHON%" -m pip --version >nul 2>nul
if not errorlevel 1 exit /b 0

set "TEMP_GET_PIP=%TEMP%\evo_get-pip.py"
call :download_file "%PIP_URL%" "%TEMP_GET_PIP%"
if errorlevel 1 exit /b 1
"%TARGET_PYTHON%" "%TEMP_GET_PIP%" --no-warn-script-location >nul 2>nul
del "%TEMP_GET_PIP%" 2>nul
if errorlevel 1 exit /b 1
exit /b 0

:install_dependencies
echo       Upgrading pip...
"%APP_PYTHON%" -m pip install --upgrade pip >nul 2>nul

echo       Installing or updating required packages...
"%APP_PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 goto :fail_install
echo       Python packages are ready.
exit /b 0

:ensure_gpu_acceleration
where nvidia-smi >nul 2>nul
if errorlevel 1 (
    echo       No NVIDIA GPU detected. Using CPU mode.
    echo       [This is normal if you do not have a dedicated graphics card]
    exit /b 0
)

echo       NVIDIA GPU detected.
"%APP_PYTHON%" -c "import torch; exit(0 if '+cu' in torch.__version__ and torch.cuda.is_available() else 1)" >nul 2>nul
if not errorlevel 1 (
    echo       GPU acceleration already active.
    exit /b 0
)

echo       Installing GPU acceleration (CUDA)...
echo       This download is large and may take several minutes.
"%APP_PYTHON%" -m pip install --force-reinstall torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124
if errorlevel 1 goto :fail_install
"%APP_PYTHON%" -m pip install --force-reinstall "numpy<2"
if errorlevel 1 goto :fail_install
echo       GPU acceleration installed.
exit /b 0

:download_file
set "DOWNLOAD_URL=%~1"
set "DOWNLOAD_DEST=%~2"
where curl.exe >nul 2>nul
if not errorlevel 1 (
    echo       Downloading with curl...
    curl.exe -L --fail --progress-bar -o "%DOWNLOAD_DEST%" "%DOWNLOAD_URL%"
    exit /b %errorlevel%
)

powershell -NoProfile -Command "exit 0" >nul 2>nul
if errorlevel 1 exit /b 1

echo       Downloading with PowerShell...
powershell -NoProfile -Command "Invoke-WebRequest -UseBasicParsing '%DOWNLOAD_URL%' -OutFile '%DOWNLOAD_DEST%'"
exit /b %errorlevel%

:preflight_checks
if not exist "requirements.txt" goto :fail_missing_requirements

echo test> ".write_test.tmp" 2>nul
if errorlevel 1 goto :fail_write_permission
del ".write_test.tmp" 2>nul

where powershell >nul 2>nul
if errorlevel 1 goto :fail_missing_powershell

set "INSTALL_DRIVE=%~d0"
set "FREE_GB=0"
call :detect_free_space_gb
if not defined FREE_GB set "FREE_GB=0"
set /a FREE_GB=!FREE_GB!+0 >nul 2>nul
if errorlevel 1 set "FREE_GB=0"
if !FREE_GB! LSS 8 goto :fail_low_disk
exit /b 0

:detect_free_space_gb
set "FREE_BYTES="
set "FREE_GB="
for /f "tokens=3" %%A in ('dir /-c "%INSTALL_DRIVE%\" ^| find "bytes "') do set "FREE_BYTES=%%A"
if not defined FREE_BYTES set "FREE_GB=0"
if defined FREE_BYTES for /f "usebackq delims=" %%A in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "[int](%FREE_BYTES% / 1GB)"`) do set "FREE_GB=%%A"
if not defined FREE_GB set "FREE_GB=0"
set /a FREE_GB=!FREE_GB!+0 >nul 2>nul
if errorlevel 1 set "FREE_GB=0"
exit /b 0

:fail_missing_requirements
echo.
echo ==========================================
echo   requirements.txt was not found!
echo ==========================================
echo.
echo   The installer cannot continue because the
echo   dependency list is missing from the folder.
echo.
echo   Make sure all project files were extracted
echo   correctly and run install.bat again.
echo.
echo ==========================================
pause
exit /b 1

:fail_write_permission
echo.
echo ==========================================
echo   Cannot write to this folder!
echo ==========================================
echo.
echo   Move the project to a writable folder such as
echo   Desktop or Documents and try again.
echo.
echo ==========================================
pause
exit /b 1

:fail_low_disk
echo.
echo ==========================================
echo   Not enough free disk space!
echo ==========================================
echo.
echo   Evo Chatterbox needs several GB for Python,
echo   dependencies, cache, and AI models.
echo.
echo   Free space detected: !FREE_GB! GB
echo   Recommended minimum before setup: 8 GB
echo   Recommended safer target: 10+ GB
echo.
echo ==========================================
pause
exit /b 1

:fail_missing_powershell
echo.
echo ==========================================
echo   PowerShell was not available!
echo ==========================================
echo.
echo   PowerShell is required to extract the
echo   portable Python package automatically.
echo.
echo   Use Windows PowerShell or place a portable
echo   Python inside:
echo   python\python.exe
echo.
echo ==========================================
pause
exit /b 1

:fail_python_download
del "%~dp0%PY_ZIP%" 2>nul
echo.
echo ==========================================
echo   Could not download portable Python!
echo ==========================================
echo.
echo   Check your internet connection and
echo   try running install.bat again.
echo.
echo   Expected download:
echo   %PY_URL%
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
echo   3. Run install.bat again or provide python\python.exe
echo.
echo   If the error persists, delete the
echo   ".venv" folder (or "python" folder)
echo   and try again.
echo.
echo ==========================================
pause
exit /b 1



