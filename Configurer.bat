@echo off
rem Change les identifiants Comptexpert / redéclare le serveur auprès de Claude.
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo ImagePME n'est pas installe : lance d'abord Installer.bat.
  pause
  exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" "scripts\configure.py"
