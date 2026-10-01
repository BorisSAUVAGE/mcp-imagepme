"""Connexion à ImagePME via le SSO CAS de l'Ordre des experts-comptables.

La session (cookies) est persistée sur disque via `storage_state` pour éviter
de repasser par le CAS à chaque appel MCP. Une nouvelle connexion n'est
retentée que si la session sauvegardée n'est plus valide.
"""

from __future__ import annotations

from playwright.sync_api import Browser, BrowserContext, Page, Playwright

from . import config


class MissingCredentialsError(RuntimeError):
    pass


def _perform_cas_login(page: Page) -> None:
    if not config.COMPTEXPERT_USERNAME or not config.COMPTEXPERT_PASSWORD:
        raise MissingCredentialsError(
            "COMPTEXPERT_USERNAME / COMPTEXPERT_PASSWORD manquants. "
            "Copie .env.example en .env et renseigne tes identifiants."
        )

    page.goto(config.IMAGEPME_DONNEES_URL, wait_until="domcontentloaded")
    # "Connexion" est un <a> sans href (géré en JS) : pas de rôle "link"
    # exposé, on cible donc par texte exact plutôt que par rôle.
    page.get_by_text("Connexion", exact=True).click()

    # Modale (Ant Design) à deux colonnes : "Accès villes" (mail/mdp direct,
    # 1er bouton "CONNEXION" du DOM) et "Accès experts-comptables"
    # (redirection CAS, 2e bouton). Confirmé en conditions réelles.
    page.get_by_role("button", name="Connexion").last.click()

    # Redirection vers identification.experts-comptables.org/cas/login
    page.wait_for_url("**/cas/login**")
    # Ids confirmés : formulaire Apereo CAS standard.
    page.locator("#username").fill(config.COMPTEXPERT_USERNAME)
    page.locator("#password").fill(config.COMPTEXPERT_PASSWORD)
    page.locator("#password").press("Enter")

    # Le CAS redirige vers /cas?ticket=... : la SPA échange ce ticket contre
    # une session via un appel async puis nettoie l'URL. Naviguer trop tôt
    # (avant la fin de cet échange) laisse la session non établie côté
    # client (observé en test : session perdue silencieusement). On attend
    # donc que le ticket disparaisse de l'URL avant de continuer.
    page.wait_for_url("**imagepme.fr/**", timeout=30_000)
    for _ in range(30):
        if "ticket=" not in page.url:
            break
        page.wait_for_timeout(500)
    page.goto(config.IMAGEPME_DONNEES_URL, wait_until="domcontentloaded")


def _is_logged_in(page: Page) -> bool:
    try:
        page.get_by_text("Vous êtes connecté", exact=False).wait_for(timeout=5_000)
        return True
    except Exception:
        return False


def get_authenticated_context(playwright: Playwright, headless: bool | None = None) -> BrowserContext:
    """Retourne un BrowserContext Playwright authentifié sur ImagePME.

    Réutilise la session persistée si elle est encore valide, sinon relance
    le flux de login CAS et sauvegarde la nouvelle session.
    """
    headless = (not config.HEADED) if headless is None else headless
    browser: Browser = playwright.chromium.launch(headless=headless)

    if config.STORAGE_STATE_PATH.exists():
        context = browser.new_context(
            storage_state=str(config.STORAGE_STATE_PATH), accept_downloads=True
        )
        page = context.new_page()
        # wait_until="load" timeout systématiquement sur cette page (une
        # ressource tierce ne finit jamais de charger) ; domcontentloaded
        # suffit largement pour lire l'état de connexion.
        page.goto(config.IMAGEPME_DONNEES_URL, wait_until="domcontentloaded")
        if _is_logged_in(page):
            page.close()
            return context
        page.close()
        context.close()

    context = browser.new_context(accept_downloads=True)
    page = context.new_page()
    _perform_cas_login(page)
    context.storage_state(path=str(config.STORAGE_STATE_PATH))
    page.close()
    return context
