@echo off
rem Met à jour mcp-imagepme depuis GitHub : double-cliquer sur ce fichier.
rem Tout tient dans un bloc ( ... ) : cmd le lit en entier avant de
rem l'exécuter, donc la mise à jour peut remplacer ce fichier sans risque.
(
  chcp 65001 >nul
  cd /d "%~dp0"
  if not exist ".venv\Scripts\python.exe" (
    echo ImagePME n'est pas installe : lance d'abord Installer.bat.
  ) else (
    ".venv\Scripts\python.exe" "scripts\update.py"
  )
  echo.
  pause
  exit /b
)
