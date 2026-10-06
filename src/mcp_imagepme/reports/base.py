"""Logique commune à tous les rapports ImagePME : ouvrir une session
authentifiée, remplir les filtres du formulaire Dash, cliquer "Rechercher"
puis un bouton de téléchargement, et récupérer le fichier produit.

Ajouter un nouveau rapport = écrire une fonction `fill(frame)` spécifique
dans reports/<nom>.py et l'appeler via `run_report`.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Callable

from playwright.sync_api import FrameLocator, sync_playwright

from .. import config
from ..auth import get_authenticated_context
from ..dash_form import get_dash_iframe

FillFn = Callable[[FrameLocator], None]

# Message affiché par ImagePME (et aucun bouton de téléchargement rendu)
# quand la requête porte sur un échantillon trop petit pour être publié.
_SECRET_STATISTIQUE_MARKER = "secret statistique"


class EchantillonInsuffisantError(RuntimeError):
    """Levée quand ImagePME refuse d'afficher un résultat (secret statistique :
    échantillon inférieur à 10 entreprises pour les filtres demandés)."""


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

            # Quand l'échantillon est trop petit, ImagePME affiche un
            # avertissement et ne rend aucun bouton de téléchargement : sans
            # ce contrôle, on attendrait bêtement 30s avant un timeout peu
            # explicite. On attend l'un ou l'autre des deux dénouements
            # possibles plutôt que de cliquer en aveugle.
            download_button = frame.locator(f"#{download_button_id}")
            warning = frame.get_by_text(_SECRET_STATISTIQUE_MARKER, exact=False)
            try:
                download_button.or_(warning).first.wait_for(timeout=15_000)
            except Exception:
                pass  # on retombe sur le comportement par défaut ci-dessous

            # Le tableau TDFC contient la légende "*S = Secret statistique" :
            # le texte seul ne prouve donc pas un refus. Seule l'absence du
            # bouton de téléchargement le confirme.
            if download_button.count() == 0 and warning.count() > 0:
                try:
                    download_button.wait_for(state="attached", timeout=3_000)
                except Exception:
                    pass
            if download_button.count() == 0 and warning.count() > 0:
                raise EchantillonInsuffisantError(
                    "ImagePME ne peut pas afficher de résultat pour ces filtres : "
                    "l'échantillon est inférieur à 10 entreprises (secret statistique). "
                    "Essaie un niveau géographique ou sectoriel plus large."
                )

            with page.expect_download() as download_info:
                download_button.click()
            download = download_info.value

            # Le nom proposé par le site ne contient que la date : deux requêtes
            # le même jour s'écraseraient. Horodatage + suffixe aléatoire (au cas
            # où deux appels partent dans la même seconde).
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            suffix = Path(download.suggested_filename).suffix
            dest = config.DOWNLOAD_DIR / f"{filename_prefix}-{stamp}-{uuid.uuid4().hex[:6]}{suffix}"
            download.save_as(dest)
            return dest
        finally:
            context.close()
