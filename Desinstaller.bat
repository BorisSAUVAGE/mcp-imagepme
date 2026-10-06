@echo off
rem Désinstalle mcp-imagepme : double-cliquer sur ce fichier.
rem Tout tient dans un bloc ( ... ) : cmd le lit en entier avant de
rem l'exécuter, donc il peut supprimer son propre dossier.
(
  chcp 65001 >nul
  set "DIR=%~dp0"
  cd /d "%~dp0"
  echo Cette operation retire ImagePME de Claude et supprime le dossier :
  echo   %~dp0
  echo y compris tes identifiants Comptexpert. Quitte d'abord completement Claude.
  echo.
  choice /c ON /m "Confirmer la desinstallation"
  if errorlevel 2 exit /b
  if exist ".venv\Scripts\python.exe" ".venv\Scripts\python.exe" "scripts\uninstall.py"
  cd /d "%TEMP%"
  rmdir /s /q "%~dp0"
  echo.
  if exist "%~dp0" (
    echo Le dossier n'a pas pu etre supprime entierement : Claude est-il bien ferme ?
  ) else (
    echo ImagePME est desinstalle.
  )
  echo Le navigateur Chromium de Playwright reste dans %LOCALAPPDATA%\ms-playwright ^(supprimable a la main^).
  pause
  exit /b
)
