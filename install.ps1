# Installation automatique de mcp-imagepme (Windows).
# Usage : double-clic sur Installer.bat, ou :
#   powershell -ExecutionPolicy Bypass -File install.ps1
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "== Installation de mcp-imagepme =="
Write-Host ""

# --- Python ------------------------------------------------------------
function Find-Python {
    foreach ($candidate in @("py", "python", "python3")) {
        if (Get-Command $candidate -ErrorAction SilentlyContinue) {
            try {
                & $candidate -c "import sys; sys.exit(sys.version_info < (3, 10))" 2>$null
                if ($LASTEXITCODE -eq 0) { return $candidate }
            } catch {}
        }
    }
    return $null
}

$PythonExe = Find-Python
if (-not $PythonExe -and (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Host "Python 3.10+ introuvable : installation via winget..."
    winget install --id Python.Python.3.12 -e --scope user --accept-package-agreements --accept-source-agreements
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "User") + ";" + [Environment]::GetEnvironmentVariable("Path", "Machine")
    $PythonExe = Find-Python
}
if (-not $PythonExe) {
    Write-Host "Python 3.10+ introuvable. Installe-le depuis https://www.python.org/downloads/ (coche 'Add python.exe to PATH') puis relance l'installation." -ForegroundColor Red
    Start-Process "https://www.python.org/downloads/"
    exit 1
}
Write-Host "Python détecté : $PythonExe"

# --- Environnement virtuel ------------------------------------------------
if (-not (Test-Path ".venv")) {
    Write-Host "Création de l'environnement virtuel (.venv)..."
    & $PythonExe -m venv .venv
} else {
    Write-Host "Environnement virtuel existant réutilisé (.venv)."
}

$VenvPy = Join-Path $ScriptDir ".venv\Scripts\python.exe"
$ImagepmeMcp = Join-Path $ScriptDir ".venv\Scripts\imagepme-mcp.exe"

# --- Dépendances ------------------------------------------------------------
Write-Host "Installation des dépendances Python..."
& $VenvPy -m pip install --upgrade pip -q
& $VenvPy -m pip install -e . -q

Write-Host "Installation du navigateur Chromium pour Playwright (peut prendre une minute)..."
& $VenvPy -m playwright install chromium

# --- Identifiants et déclaration auprès de Claude ----------------------------
Write-Host ""
Write-Host "Ouverture de la fenêtre de configuration..."
& $VenvPy scripts\configure.py

Write-Host ""
Write-Host "Installation terminée."
