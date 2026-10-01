"""Serveur MCP ImagePME.

Pour ajouter un nouveau rapport plus tard : écrire reports/<nom>.py (sur le
modèle de reports/tva.py ou reports/tdfc.py) puis exposer une fonction ici
avec @mcp.tool().
"""

from __future__ import annotations

import asyncio

from mcp.server.fastmcp import FastMCP

from .reports.tdfc import TRANCHE_CA_TOUTES, download_tdfc_excel
from .reports.tva import download_tva_excel

mcp = FastMCP("imagepme")


@mcp.tool()
async def get_indicateurs_tva(
    periodicite: str,
    annee: str,
    periode: str,
    niveau_sectoriel: str = "tous",
    secteur: str | None = None,
    niveau_geo: str = "national",
    territoire: str | None = None,
) -> str:
    """Télécharge le fichier Excel des indicateurs TVA (ICA/ICAC) d'ImagePME.

    Args:
        periodicite: "mensuelle" ou "trimestrielle".
        annee: année de la période recherchée (ex. "2026").
        periode: nom du mois (ex. "Mai") si mensuelle, ou trimestre
            ("T1".."T4") si trimestrielle.
        niveau_sectoriel: "ape", "classe", "groupe", "division", "section"
            ou "tous" (défaut).
        secteur: libellé du secteur précis, requis si niveau_sectoriel != "tous".
        niveau_geo: "national" (défaut), "region" ou "departement".
        territoire: nom de la région/du département, requis si niveau_geo != "national".

    Returns:
        Le chemin local du fichier Excel téléchargé.
    """
    # download_tva_excel utilise Playwright en mode synchrone, incompatible
    # avec la boucle asyncio du serveur MCP : on l'exécute dans un thread à part.
    path = await asyncio.to_thread(
        download_tva_excel,
        periodicite=periodicite,
        annee=annee,
        periode=periode,
        niveau_sectoriel=niveau_sectoriel,
        secteur=secteur,
        niveau_geo=niveau_geo,
        territoire=territoire,
    )
    return str(path)


@mcp.tool()
async def get_indicateurs_tdfc(
    tranche_ca: str = TRANCHE_CA_TOUTES,
    niveau_sectoriel: str = "tous",
    secteur: str | None = None,
    niveau_geo: str = "national",
    territoire: str | None = None,
) -> str:
    """Télécharge le fichier Excel des indicateurs TDFC (données fiscales
    annuelles) d'ImagePME.

    Args:
        tranche_ca: libellé de la tranche de chiffre d'affaires annuel
            (défaut : toutes tranches confondues).
        niveau_sectoriel: "ape", "classe", "groupe", "division", "section"
            ou "tous" (défaut).
        secteur: libellé du secteur précis, requis si niveau_sectoriel != "tous".
        niveau_geo: "national" (défaut), "region" ou "departement".
        territoire: nom de la région/du département, requis si niveau_geo != "national".

    Returns:
        Le chemin local du fichier Excel téléchargé.
    """
    path = await asyncio.to_thread(
        download_tdfc_excel,
        tranche_ca=tranche_ca,
        niveau_sectoriel=niveau_sectoriel,
        secteur=secteur,
        niveau_geo=niveau_geo,
        territoire=territoire,
    )
    return str(path)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
