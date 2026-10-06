#!/bin/bash
# Désinstalle mcp-imagepme (macOS) : double-cliquer sur ce fichier.
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR" || exit 1
echo "Cette opération retire ImagePME de Claude et supprime le dossier :"
echo "  $DIR"
echo "y compris tes identifiants Comptexpert. Quitte d'abord complètement Claude."
echo
read -r -p "Confirmer la désinstallation ? (o/N) " answer
if [ "$answer" != "o" ] && [ "$answer" != "O" ]; then
  echo "Annulé."
  exit 0
fi
[ -x .venv/bin/python ] && ./.venv/bin/python scripts/uninstall.py
cd / && rm -rf "$DIR"
echo
echo "ImagePME est désinstallé."
echo "Le navigateur Chromium de Playwright reste dans ~/Library/Caches/ms-playwright (supprimable à la main)."
read -r -p "Appuie sur Entrée pour fermer cette fenêtre."
