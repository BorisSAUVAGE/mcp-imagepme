"""Rapport "Indicateurs TVA (ICA et ICAC)" d'ImagePME.

Champs du formulaire (voir capture d'écran de référence) :
- Périodicité* : Mensuelle / Trimestrielle
- Niveau sectoriel / secteur* : granularité + secteur précis
- Période* : année + mois (ou trimestre selon la périodicité)
- Niveau géographique* : National / Régions / Départements + territoire précis
"""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import FrameLocator

from ..dash_form import select_dropdown, select_radio
from .base import run_report

NIVEAUX_SECTORIELS = {
    "ape": "Code APE - découpage en 732 secteurs",
    "classe": "Classe - 615 secteurs",
    "groupe": "Groupe - 272 secteurs",
    "division": "Division - 88 secteurs",
    "section": "Section - 21 secteurs",
    "tous": "Tous secteurs confondus",
}

NIVEAUX_GEO = {
    "national": "National",
    "region": "Régions",
    "departement": "Départements",
}

# Ids des composants Dash, tous confirmés en conditions réelles.
_ID_PERIODE_YEAR = "tva_periode_year"
_ID_PERIODE_MONTH = "tva_periode_month"
_ID_SECTEUR_NIVEAU = "tva_niveau_secteur"
_ID_SECTEUR = "tva_secteur"
_ID_GEO_NIVEAU = "tva_niveau_geographique"
_ID_GEO_TERRITOIRE = "tva_territoire"
_ID_SEARCH_BUTTON = "update_tva"
_ID_DOWNLOAD_EXCEL = "download_tva_excel"
_ID_DOWNLOAD_PDF = "download_tva_pdf"


def _download_tva(
    download_button_id: str,
    filename_prefix: str,
    periodicite: str,
    annee: str,
    periode: str,
    niveau_sectoriel: str,
    secteur: str | None,
    niveau_geo: str,
    territoire: str | None,
) -> Path:
    def fill(frame: FrameLocator) -> None:
        select_radio(frame, "Mensuelle" if periodicite == "mensuelle" else "Trimestrielle")
        select_dropdown(frame, _ID_SECTEUR_NIVEAU, NIVEAUX_SECTORIELS[niveau_sectoriel])
        if secteur and niveau_sectoriel != "tous":
            select_dropdown(frame, _ID_SECTEUR, secteur)
        select_dropdown(frame, _ID_PERIODE_YEAR, annee)
        select_dropdown(frame, _ID_PERIODE_MONTH, periode)
        select_dropdown(frame, _ID_GEO_NIVEAU, NIVEAUX_GEO[niveau_geo])
        if territoire and niveau_geo != "national":
            select_dropdown(frame, _ID_GEO_TERRITOIRE, territoire)

    return run_report(
        fill,
        search_button_id=_ID_SEARCH_BUTTON,
        download_button_id=download_button_id,
        filename_prefix=filename_prefix,
    )


def download_tva_excel(
    periodicite: str,
    annee: str,
    periode: str,
    niveau_sectoriel: str = "tous",
    secteur: str | None = None,
    niveau_geo: str = "national",
    territoire: str | None = None,
) -> Path:
    """Télécharge le fichier Excel des indicateurs TVA pour les filtres donnés.

    periodicite: "mensuelle" ou "trimestrielle"
    periode: nom du mois (ex. "Mai", "Juillet-Août") si mensuelle,
        ou trimestre ("T1".."T4") si trimestrielle
    niveau_sectoriel: une des clés de NIVEAUX_SECTORIELS
    secteur: libellé du secteur précis (ignoré si niveau_sectoriel == "tous")
    niveau_geo: une des clés de NIVEAUX_GEO
    territoire: nom de la région/du département (ignoré si niveau_geo == "national")
    """
    return _download_tva(
        _ID_DOWNLOAD_EXCEL, "tva", periodicite, annee, periode, niveau_sectoriel, secteur, niveau_geo, territoire
    )


def download_tva_pdf(
    periodicite: str,
    annee: str,
    periode: str,
    niveau_sectoriel: str = "tous",
    secteur: str | None = None,
    niveau_geo: str = "national",
    territoire: str | None = None,
) -> Path:
    """Télécharge le fichier PDF des indicateurs TVA pour les filtres donnés
    (mêmes paramètres que download_tva_excel)."""
    return _download_tva(
        _ID_DOWNLOAD_PDF, "tva", periodicite, annee, periode, niveau_sectoriel, secteur, niveau_geo, territoire
    )
