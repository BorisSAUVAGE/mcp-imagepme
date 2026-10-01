"""Helpers génériques pour piloter les widgets Dash (Plotly) de l'app
ImagePME, embarquée en iframe cross-origin dans /donnees.

Ces composants sont des react-select "classic" (classes CSS `Select-*`,
confirmées par le JS clientside vu dans le HTML de l'app : `.Select-value-label`).
Écrire ces helpers une seule fois ici permet d'ajouter facilement de
nouveaux rapports/filtres sans réécrire la logique de sélection.
"""

from __future__ import annotations

from playwright.sync_api import FrameLocator


def select_dropdown(frame: FrameLocator, dropdown_id: str, option_text: str) -> None:
    """Ouvre un dropdown react-select (par id de composant Dash) et choisit
    l'option dont le texte visible correspond à `option_text`."""
    control = frame.locator(f"#{dropdown_id}")
    control.click()
    # Selon le nombre d'options, Dash rend soit des `.Select-option` (liste
    # courte), soit des `.VirtualizedSelectOption` (react-virtualized, pour
    # les longues listes, ex. les 732 codes APE). On cherche par texte
    # visible dans le menu ouvert plutôt que par classe, pour couvrir les
    # deux cas sans dépendre d'un détail d'implémentation.
    frame.locator(".Select-menu-outer").get_by_text(option_text, exact=True).first.click()


def select_radio(frame: FrameLocator, label_text: str) -> None:
    """Sélectionne un bouton radio Dash (dcc.RadioItems) via le texte de son
    label."""
    frame.get_by_text(label_text, exact=True).click()


def get_dash_iframe(page) -> FrameLocator:
    """Retourne le FrameLocator de l'app Dash embarquée dans /donnees.

    Confirmé en conditions réelles : l'app est servie sur un sous-domaine
    tiers (node9.datakkod.com/webapp/45205/...) avec un token de session
    signé en query string. On cible l'iframe via un fragment stable de son
    URL plutôt que sa position, plus robuste si d'autres iframes apparaissent.
    """
    return page.frame_locator("iframe[src*='/webapp/']")
