# Installation automatique de mcp-imagepme (Windows).
# Usage : clic droit > "Exécuter avec PowerShell", ou :
#   powershell -ExecutionPolicy Bypass -File install.ps1
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "== Installation de mcp-imagepme =="
Write-Host ""

# --- Python ------------------------------------------------------------
$PythonExe = $null
foreach ($candidate in @("py", "python", "python3")) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) {
        $PythonExe = $candidate
        break
    }
}
if (-not $PythonExe) {
    Write-Error "Python 3.10+ introuvable. Installe-le depuis https://www.python.org/downloads/ (coche 'Add python.exe to PATH') puis relance ce script."
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

# --- Identifiants ------------------------------------------------------------
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host ""
    Write-Host "Identifiants Comptexpert (laisse vide pour compléter .env toi-même plus tard) :"
    $ceUser = Read-Host "  Email"
    if ($ceUser) {
        $cePassSecure = Read-Host "  Mot de passe" -AsSecureString
        $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($cePassSecure)
        try {
            $cePass = [Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
        } finally {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
        }
        $envContent = Get-Content ".env" | ForEach-Object {
            if ($_ -match "^COMPTEXPERT_USERNAME=") { "COMPTEXPERT_USERNAME=$ceUser" }
            elseif ($_ -match "^COMPTEXPERT_PASSWORD=") { "COMPTEXPERT_PASSWORD=$cePass" }
            else { $_ }
        }
        Set-Content ".env" $envContent
        Write-Host "Identifiants enregistrés dans .env."
    } else {
        Write-Host "Pense à compléter .env avec tes identifiants avant la première utilisation."
    }
} else {
    Write-Host ".env existe déjà, inchangé."
}

# --- Déclaration auprès de Claude Code --------------------------------------
Write-Host ""
if (Get-Command claude -ErrorAction SilentlyContinue) {
    Write-Host "Déclaration du serveur MCP auprès de Claude Code..."
    & claude mcp add imagepme -- "$ImagepmeMcp"
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "'claude mcp add' a échoué (peut-être déjà déclaré). Vérifie avec /mcp dans Claude Code, ou ajoute-le manuellement (voir .mcp.json.example)."
    }
} else {
    Write-Host "Commande 'claude' introuvable dans le PATH."
    Write-Host "Ajoute le serveur manuellement : copie .mcp.json.example en .mcp.json et renseigne :"
    Write-Host "  $ImagepmeMcp"
}

Write-Host ""
Write-Host "Installation terminée. (Re)démarre Claude Code, ou reconnecte via /mcp, pour activer le serveur imagepme."
