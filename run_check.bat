@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_EXE="
where py >nul 2>&1 && set "PYTHON_EXE=py -3"
if not defined PYTHON_EXE (
  where python >nul 2>&1 && set "PYTHON_EXE=python"
)

if not defined PYTHON_EXE (
  echo Python launcher not found. Install Python 3 and ensure ^`py^` or ^`python^` is on PATH.
  exit /b 1
)

%PYTHON_EXE% --version 2>&1
echo ---
%PYTHON_EXE% -m venv venv_new 2>&1
if errorlevel 1 exit /b %errorlevel%
echo Venv created
"%CD%\venv_new\Scripts\python.exe" --version 2>&1
echo ---
"%CD%\venv_new\Scripts\pip.exe" install -r requirements.txt 2>&1
echo Install done
endlocal
