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
if ! "$PYTHON_BIN" -c 'import sys; sys.exit(sys.version_info < (3, 10))'; then
  echo "Erreur : Python $PYVER est trop ancien, il faut Python 3.10 ou plus." >&2
  echo "Installe-le depuis https://www.python.org/downloads/ puis relance ce script." >&2
  exit 1
fi
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

# --- Identifiants et déclaration auprès de Claude ----------------------------
echo
echo "Ouverture de la fenêtre de configuration…"
"$VENV_PY" scripts/configure.py

echo
echo "Installation terminée."
