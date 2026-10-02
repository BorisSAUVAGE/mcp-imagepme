"""Helpers génériques pour piloter les widgets Dash (Plotly) de l'app
ImagePME, embarquée en iframe cross-origin dans /donnees.

Ces composants sont des react-select "classic" (classes CSS `Select-*`,
confirmées par le JS clientside vu dans le HTML de l'app : `.Select-value-label`).
Écrire ces helpers une seule fois ici permet d'ajouter facilement de
nouveaux rapports/filtres sans réécrire la logique de sélection.
"""

from __future__ import annotations

import re

from playwright.sync_api import FrameLocator

# Code NAF/APE sans point (ex. "1071C"), pour le reformater au format
# officiel pointé ("10.71C") utilisé dans les libellés du site.
_NAF_CODE_NO_DOT = re.compile(r"^(\d{2})(\d{2})([A-Za-z])$")


class OptionNotFoundError(ValueError):
    """Levée quand aucune option d'un dropdown ne correspond au texte fourni."""


def _search_candidates(option_text: str) -> list[str]:
    """Variantes à essayer successivement pour `option_text`, de la plus
    fidèle à la plus permissive. Couvre les erreurs de format les plus
    courantes (code NAF non pointé, code+libellé combinés) sans exiger le
    libellé exact tel qu'affiché sur le site."""
    candidates = [option_text]

    if " - " in option_text:
        # Ex. "1071C - Boulangerie..." -> retente avec juste le libellé,
        # utile si seul le préfixe de code ne correspond pas au format réel.
        candidates.append(option_text.split(" - ", 1)[1])

    m = _NAF_CODE_NO_DOT.match(option_text.strip())
    if m:
        candidates.append(f"{m.group(1)}.{m.group(2)}{m.group(3).upper()}")

    return candidates


def select_dropdown(frame: FrameLocator, dropdown_id: str, option_text: str) -> None:
    """Ouvre un dropdown react-select (par id de composant Dash) et choisit
    l'option correspondant à `option_text`.

    Pour les longues listes (ex. les 732 codes APE), Dash virtualise les
    options : celles non visibles à l'écran n'existent pas dans le DOM tant
    qu'on n'a pas scrollé jusqu'à elles. Plutôt que de chercher un texte
    exact parmi les options déjà rendues (fragile : ça loupe les options non
    rendues, et n'accepte aucune variation de libellé), on tape dans le
    champ de recherche du dropdown — react-select filtre alors nativement,
    exactement comme le ferait un utilisateur. Ça tolère un simple code
    ("10.71C"), un mot-clé ("Boulangerie") ou le libellé complet, insensible
    à la casse, avec quelques repêchages automatiques (cf. _search_candidates)
    pour les formats de code approximatifs.
    """
    # Un dropdown dépendant d'un autre (ex. le mois dépend de l'année, le
    # secteur précis dépend du niveau sectoriel) passe par un état de
    # chargement (`data-dash-is-loading="true"`) pendant que Dash recalcule
    # ses options côté serveur ; ses options sont vides tant que ça dure.
    # Si on interagit trop tôt, on tape dans un champ qui n'a pas encore
    # reçu sa vraie liste d'options.
    frame.locator(f"#{dropdown_id}[data-dash-is-loading='true']").wait_for(state="detached", timeout=15_000)

    control = frame.locator(f"#{dropdown_id}")
    control.click()
    search_input = frame.locator(f"#{dropdown_id} input[role='combobox']")

    menu = frame.locator(".Select-menu-outer")
    no_results = menu.locator(".Select-noresults")
    option = menu.locator(".Select-option, .VirtualizedSelectOption")

    for candidate in _search_candidates(option_text):
        search_input.fill(candidate)
        option.or_(no_results).first.wait_for(timeout=10_000)
        if option.count() > 0:
            option.first.click()
            return

    raise OptionNotFoundError(
        f"Aucune option ne correspond à {option_text!r} dans le dropdown #{dropdown_id}. "
        "Essaie un code (format NAF pointé, ex. '10.71C'), un mot-clé du libellé, "
        "ou un libellé plus court."
    )


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
