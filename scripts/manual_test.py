"""Script de mise au point : lance le flow TVA en mode visible (headed) pour
ajuster les sélecteurs Playwright en conditions réelles, sans passer par un
client MCP.

Usage :
    MCP_IMAGEPME_HEADED=1 python scripts/manual_test.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mcp_imagepme.reports.tva import download_tva_excel  # noqa: E402

if __name__ == "__main__":
    path = download_tva_excel(
        periodicite="mensuelle",
        annee="2026",
        periode="Mai",
        niveau_sectoriel="tous",
        niveau_geo="national",
    )
    print(f"Fichier téléchargé : {path}")
