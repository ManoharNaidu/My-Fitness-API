@echo off
cd /d "D:\Backends\My Fitness API"
"D:\Program Files\python.exe" --version 2>&1
echo ---
"D:\Program Files\python.exe" -m venv venv_new 2>&1
echo Venv created
"D:\Backends\My Fitness API\venv_new\Scripts\python.exe" --version 2>&1
echo ---
"D:\Backends\My Fitness API\venv_new\Scripts\pip.exe" install -r requirements.txt 2>&1
echo Install done
