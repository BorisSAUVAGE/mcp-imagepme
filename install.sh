#!/usr/bin/env bash
# Installation automatique de mcp-imagepme (macOS / Linux).
# Usage : ./install.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "== Installation de mcp-imagepme =="
echo

# --- Python ---------------------------------------------------------------
PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Erreur : '$PYTHON_BIN' introuvable." >&2
  echo "Installe Python 3.10+ depuis https://www.python.org/downloads/ puis relance ce script." >&2
  exit 1
fi

PYVER="$("$PYTHON_BIN" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
echo "Python détecté : $PYVER ($PYTHON_BIN)"

# --- Environnement virtuel --------------------------------------------------
if [ ! -d .venv ]; then
  echo "Création de l'environnement virtuel (.venv)..."
  "$PYTHON_BIN" -m venv .venv
else
  echo "Environnement virtuel existant réutilisé (.venv)."
fi

VENV_PY="$SCRIPT_DIR/.venv/bin/python"
VENV_BIN="$SCRIPT_DIR/.venv/bin"

# --- Dépendances ------------------------------------------------------------
echo "Installation des dépendances Python..."
"$VENV_PY" -m pip install --upgrade pip -q
"$VENV_PY" -m pip install -e . -q

echo "Installation du navigateur Chromium pour Playwright (peut prendre une minute)..."
"$VENV_PY" -m playwright install chromium

# --- Identifiants ------------------------------------------------------------
if [ ! -f .env ]; then
  cp .env.example .env
  echo
  echo "Identifiants Comptexpert (laisse vide pour compléter .env toi-même plus tard) :"
  read -r -p "  Email : " CE_USER
  read -r -s -p "  Mot de passe : " CE_PASS
  echo
  if [ -n "$CE_USER" ]; then
    CE_USER="$CE_USER" CE_PASS="$CE_PASS" awk '
      /^COMPTEXPERT_USERNAME=/ { print "COMPTEXPERT_USERNAME=" ENVIRON["CE_USER"]; next }
      /^COMPTEXPERT_PASSWORD=/ { print "COMPTEXPERT_PASSWORD=" ENVIRON["CE_PASS"]; next }
      { print }
    ' .env > .env.tmp && mv .env.tmp .env
    echo "Identifiants enregistrés dans .env."
  else
    echo "Pense à compléter .env avec tes identifiants avant la première utilisation."
  fi
  unset CE_USER CE_PASS
else
  echo ".env existe déjà, inchangé."
fi

# --- Déclaration auprès de Claude Code --------------------------------------
echo
if command -v claude >/dev/null 2>&1; then
  echo "Déclaration du serveur MCP auprès de Claude Code..."
  if ! claude mcp add imagepme -- "$VENV_BIN/imagepme-mcp"; then
    echo "Avertissement : 'claude mcp add' a échoué (peut-être déjà déclaré)." >&2
    echo "Vérifie avec /mcp dans Claude Code, ou ajoute-le manuellement (voir .mcp.json.example)." >&2
  fi
else
  echo "Commande 'claude' introuvable dans le PATH."
  echo "Ajoute le serveur manuellement : copie .mcp.json.example en .mcp.json et renseigne :"
  echo "  $VENV_BIN/imagepme-mcp"
fi

echo
echo "Installation terminée. (Re)démarre Claude Code, ou reconnecte via /mcp, pour activer le serveur imagepme."
