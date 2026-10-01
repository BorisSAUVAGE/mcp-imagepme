"""Rapport "Indicateurs TDFC" d'ImagePME (données fiscales annuelles,
année figée par le site — pas de sélecteur de période).

Champs du formulaire :
- Niveau sectoriel / secteur* : granularité + secteur précis
- Tranche de CA annuel*
- Niveau géographique* : National / Régions / Départements + territoire précis
"""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import FrameLocator

from ..dash_form import select_dropdown
from .base import run_report
from .tva import NIVEAUX_GEO, NIVEAUX_SECTORIELS

# Ids des composants Dash, tous confirmés en conditions réelles (l'onglet
# TDFC ne rend ses vrais composants qu'une fois cliqué/actif).
_ID_SECTEUR_NIVEAU = "tdfc_niveau_secteur"
_ID_SECTEUR = "tdfc_secteur"
_ID_TRANCHE_CA = "tdfc_trancheca"
_ID_GEO_NIVEAU = "tdfc_niveau_geographique"
_ID_GEO_TERRITOIRE = "tdfc_territoire"
_ID_TAB_BUTTON = "button_tdfc"
_ID_SEARCH_BUTTON = "update_tdfc"
_ID_DOWNLOAD_EXCEL = "download_tdfc_excel"

# Valeur par défaut vue à l'écran ; la liste complète des tranches sera à
# compléter une fois le dropdown inspecté en direct.
TRANCHE_CA_TOUTES = "Toutes tranches de CA"


def download_tdfc_excel(
    tranche_ca: str = TRANCHE_CA_TOUTES,
    niveau_sectoriel: str = "tous",
    secteur: str | None = None,
    niveau_geo: str = "national",
    territoire: str | None = None,
) -> Path:
    """Télécharge le fichier Excel des indicateurs TDFC pour les filtres donnés.

    tranche_ca: libellé de la tranche de chiffre d'affaires annuel
    niveau_sectoriel: une des clés de NIVEAUX_SECTORIELS (cf. reports.tva)
    secteur: libellé du secteur précis (ignoré si niveau_sectoriel == "tous")
    niveau_geo: une des clés de NIVEAUX_GEO (cf. reports.tva)
    territoire: nom de la région/du département (ignoré si niveau_geo == "national")
    """

    def fill(frame: FrameLocator) -> None:
        frame.locator(f"#{_ID_TAB_BUTTON}").click()  # onglet TDFC (TVA actif par défaut)
        select_dropdown(frame, _ID_SECTEUR_NIVEAU, NIVEAUX_SECTORIELS[niveau_sectoriel])
        if secteur and niveau_sectoriel != "tous":
            select_dropdown(frame, _ID_SECTEUR, secteur)
        select_dropdown(frame, _ID_TRANCHE_CA, tranche_ca)
        select_dropdown(frame, _ID_GEO_NIVEAU, NIVEAUX_GEO[niveau_geo])
        if territoire and niveau_geo != "national":
            select_dropdown(frame, _ID_GEO_TERRITOIRE, territoire)

    return run_report(
        fill,
        search_button_id=_ID_SEARCH_BUTTON,
        download_button_id=_ID_DOWNLOAD_EXCEL,
        filename_prefix="tdfc",
    )
