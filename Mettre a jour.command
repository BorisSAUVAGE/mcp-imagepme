#!/bin/bash
# Met à jour mcp-imagepme depuis GitHub (macOS) : double-cliquer sur ce fichier.
cd "$(dirname "$0")" && ./.venv/bin/python scripts/update.py
echo
read -r -p "Appuie sur Entrée pour fermer cette fenêtre."
