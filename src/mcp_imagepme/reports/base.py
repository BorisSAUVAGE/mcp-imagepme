"""Logique commune à tous les rapports ImagePME : ouvrir une session
authentifiée, remplir les filtres du formulaire Dash, cliquer "Rechercher"
puis un bouton de téléchargement, et récupérer le fichier produit.

Ajouter un nouveau rapport = écrire une fonction `fill(frame)` spécifique
dans reports/<nom>.py et l'appeler via `run_report`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from playwright.sync_api import FrameLocator, sync_playwright

from .. import config
from ..auth import get_authenticated_context
from ..dash_form import get_dash_iframe

FillFn = Callable[[FrameLocator], None]


def run_report(
    fill: FillFn,
    search_button_id: str,
    download_button_id: str,
    filename_prefix: str,
) -> Path:
    """Exécute un cycle complet : login (ou réutilisation de session) ->
    remplissage des filtres -> recherche -> téléchargement.

    Les ids des boutons (ex. "update_tva", "download_tva_excel") sont ceux
    des composants Dash, confirmés en conditions réelles.

    Retourne le chemin local du fichier téléchargé.
    """
    with sync_playwright() as playwright:
        context = get_authenticated_context(playwright)
        try:
            page = context.new_page()
            page.goto(config.IMAGEPME_DONNEES_URL, wait_until="domcontentloaded")
            frame = get_dash_iframe(page)

            fill(frame)
            frame.locator(f"#{search_button_id}").click()

            with page.expect_download() as download_info:
                frame.locator(f"#{download_button_id}").click()
            download = download_info.value

            dest = config.DOWNLOAD_DIR / f"{filename_prefix}-{download.suggested_filename}"
            download.save_as(dest)
            return dest
        finally:
            context.close()
