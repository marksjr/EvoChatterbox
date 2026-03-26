@echo off
setlocal
title Evo Chatterbox Portable
cd /d "%~dp0"

echo ==========================================
echo   Evo Chatterbox Portable para Windows
echo ==========================================
echo.

set "BOOTSTRAP_PYTHON="
if exist "%~dp0python\python.exe" set "BOOTSTRAP_PYTHON=%~dp0python\python.exe"
if not defined BOOTSTRAP_PYTHON if exist "%~dp0runtime\python.exe" set "BOOTSTRAP_PYTHON=%~dp0runtime\python.exe"
if not defined BOOTSTRAP_PYTHON (
    where python >nul 2>nul
    if errorlevel 1 goto :python_missing
    set "BOOTSTRAP_PYTHON=python"
)

echo Python usado para inicializacao:
echo %BOOTSTRAP_PYTHON%
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [1/6] Preparando ambiente local...
    "%BOOTSTRAP_PYTHON%" -m venv .venv
    if errorlevel 1 goto :fail
)

if not exist ".cache\huggingface\hub" mkdir ".cache\huggingface\hub"
if not exist ".cache\pkuseg" mkdir ".cache\pkuseg"
if not exist "output" mkdir "output"

set "HF_HOME=%cd%\.cache\huggingface"
set "HUGGINGFACE_HUB_CACHE=%cd%\.cache\huggingface\hub"
set "PKUSEG_HOME=%cd%\.cache\pkuseg"
set "HF_HUB_DISABLE_SYMLINKS_WARNING=1"

echo [2/6] Instalando dependencias do aplicativo...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :fail

where nvidia-smi >nul 2>nul
if errorlevel 1 goto :start_server

echo [3/6] GPU NVIDIA detectada. Verificando suporte CUDA...
".venv\Scripts\python.exe" -c "import torch; print(torch.__version__); print(torch.cuda.is_available())" > ".cuda_check.tmp" 2>nul
findstr /C:"+cu124" ".cuda_check.tmp" >nul
if errorlevel 1 goto :install_cuda
findstr /C:"True" ".cuda_check.tmp" >nul
if errorlevel 1 goto :install_cuda
goto :start_server

:install_cuda
echo [4/6] Instalando aceleracao por GPU...
".venv\Scripts\python.exe" -m pip install --force-reinstall torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124
if errorlevel 1 goto :fail
".venv\Scripts\python.exe" -m pip install --force-reinstall "numpy<2"
if errorlevel 1 goto :fail

:start_server
del ".cuda_check.tmp" 2>nul

echo [5/6] Iniciando o servidor local...
start "Evo Chatterbox Server" cmd /k ".venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000"

echo [6/6] Aguardando abertura da interface...
powershell -NoProfile -Command "$deadline=(Get-Date).AddSeconds(90); while((Get-Date) -lt $deadline){ try { Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8000/health' | Out-Null; exit 0 } catch { Start-Sleep -Milliseconds 800 } }; exit 1"
if errorlevel 1 goto :fail_server

start "" "http://127.0.0.1:8000/"
echo.
echo Interface aberta no navegador.
echo Se quiser encerrar o sistema, feche a janela "Evo Chatterbox Server".
exit /b 0

:python_missing
echo Python nao foi encontrado neste computador.
echo.
echo O sistema aceita dois modos:
echo 1. Colocar um Python portable em `.\\python\\python.exe`
echo 2. Instalar o Python 3.11 e marcar "Add Python to PATH"
echo Link oficial:
echo https://www.python.org/downloads/windows/
echo.
pause
exit /b 1

:fail_server
echo.
echo O servidor nao respondeu a tempo.
echo Verifique a janela "Evo Chatterbox Server".
pause
exit /b 1

:fail
echo.
echo Falha ao preparar ou iniciar o sistema.
echo Se o erro persistir, feche esta janela e abra novamente o arquivo INICIAR.bat.
pause
exit /b 1

