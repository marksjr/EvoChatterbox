@echo off
setlocal enabledelayedexpansion
title Evo Chatterbox
cd /d "%~dp0"
chcp 65001 >nul 2>nul

echo.
echo ==========================================
echo   Evo Chatterbox
echo ==========================================
echo.

:: ------------------------------------------
::  Check if installed
:: ------------------------------------------
if not exist ".installed" (
    echo   First time detected. Running setup...
    echo.
    call "%~dp0install.bat"
    if errorlevel 1 exit /b 1
)

:: ------------------------------------------
::  Determine which Python to use
:: ------------------------------------------
set "APP_PYTHON="
set /p INSTALL_MODE=<".installed"

:: Trim whitespace from INSTALL_MODE
for /f "tokens=*" %%a in ("!INSTALL_MODE!") do set "INSTALL_MODE=%%a"

if "!INSTALL_MODE!"=="embed" (
    if exist "%~dp0python\python.exe" (
        set "APP_PYTHON=%~dp0python\python.exe"
    ) else (
        echo   Portable Python missing. Running setup...
        del ".installed" 2>nul
        call "%~dp0install.bat"
        if errorlevel 1 exit /b 1
        set /p INSTALL_MODE=<".installed"
    )
)

if not defined APP_PYTHON (
    if exist ".venv\Scripts\python.exe" (
        set "APP_PYTHON=%cd%\.venv\Scripts\python.exe"
    ) else (
        echo   Environment missing. Running setup...
        del ".installed" 2>nul
        call "%~dp0install.bat"
        if errorlevel 1 exit /b 1
        :: Re-read mode after install
        set /p INSTALL_MODE=<".installed"
        for /f "tokens=*" %%a in ("!INSTALL_MODE!") do set "INSTALL_MODE=%%a"
        if "!INSTALL_MODE!"=="embed" (
            set "APP_PYTHON=%~dp0python\python.exe"
        ) else (
            set "APP_PYTHON=%cd%\.venv\Scripts\python.exe"
        )
    )
)

:: ------------------------------------------
::  Set environment variables
:: ------------------------------------------
if not exist ".cache\huggingface\hub" mkdir ".cache\huggingface\hub"
if not exist ".cache\pkuseg" mkdir ".cache\pkuseg"
if not exist "output" mkdir "output"

set "HF_HOME=%cd%\.cache\huggingface"
set "HUGGINGFACE_HUB_CACHE=%cd%\.cache\huggingface\hub"
set "PKUSEG_HOME=%cd%\.cache\pkuseg"
set "HF_HUB_DISABLE_SYMLINKS_WARNING=1"

:: ------------------------------------------
::  Check for dependency updates
:: ------------------------------------------
echo   Starting with: !APP_PYTHON!
echo.

:: ------------------------------------------
::  Start server
:: ------------------------------------------
echo   Starting local server...
echo   [First model load may take a while]
echo.
start "Evo Chatterbox Server" cmd /k "title Evo Chatterbox Server && "!APP_PYTHON!" -m uvicorn app:app --host 127.0.0.1 --port 8000"

echo   Waiting for server to be ready...
powershell -NoProfile -Command "$deadline=(Get-Date).AddSeconds(120); while((Get-Date) -lt $deadline){ try { Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8000/health' | Out-Null; exit 0 } catch { Write-Host -NoNewline '.'; Start-Sleep -Milliseconds 1000 } }; exit 1"
echo.

if errorlevel 1 goto :fail_server

start "" "http://127.0.0.1:8000/"
echo.
echo ==========================================
echo   Browser opened!
echo ==========================================
echo.
echo   To stop: close the window titled
echo   "Evo Chatterbox Server"
echo.
echo   To restart: run start.bat again.
echo.
echo ==========================================
exit /b 0

:: ==========================================
::   Error Messages
:: ==========================================
:fail_server
echo.
echo ==========================================
echo   Server did not respond!
echo ==========================================
echo.
echo   Check the "Evo Chatterbox Server"
echo   window for error details.
echo.
echo   Possible causes:
echo   - Port 8000 is in use by another program
echo   - Not enough RAM
echo   - Model still loading (try waiting)
echo.
echo   Try:
echo   1. Close other heavy programs
echo   2. Run start.bat again
echo.
echo ==========================================
pause
exit /b 1
