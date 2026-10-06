# mcp-imagepme

Serveur MCP (Model Context Protocol) qui donne accès aux indicateurs
[ImagePME](https://www.imagepme.fr/donnees) (baromètre économique de l'Ordre
des experts-comptables) depuis un assistant compatible MCP (Claude Code,
Claude Desktop, etc.).

Le site ne propose ni API ni export automatisable classique : les données
sont générées via un formulaire (Plotly Dash) accessible uniquement aux
experts-comptables connectés. Ce serveur pilote donc un vrai navigateur
(Playwright) pour se connecter, remplir le formulaire et récupérer le
fichier Excel produit — exactement comme le ferait un utilisateur humain.

**Prérequis indispensable : un compte Comptexpert valide** (identifiants de
connexion au portail de l'Ordre des experts-comptables). Ce projet ne
fournit aucun accès aux données — chaque utilisateur doit avoir son propre
compte, et n'utilise que ses propres droits d'accès.

## Installation (sans terminal)

Prérequis : [Python 3.10+](https://www.python.org/downloads/) (sous
Windows, l'installeur l'installe tout seul s'il manque) et l'application
[Claude](https://claude.ai/download).

1. Télécharge le projet : bouton vert **Code → Download ZIP** sur
   [la page GitHub](https://github.com/BorisSAUVAGE/mcp-imagepme), puis
   décompresse-le dans ton dossier personnel (pas dans Téléchargements).
2. Double-clique sur l'installeur :
   - **Windows** : `Installer.bat` (si Windows affiche « Windows a protégé
     votre ordinateur », clique sur *Informations complémentaires → Exécuter
     quand même*) ;
   - **macOS** : `Installer.command` (la première fois, clic droit →
     *Ouvrir*, puis confirmer).
3. Une fenêtre s'ouvre : saisis ton identifiant et ton mot de passe Comptexpert,
   coche où activer ImagePME (Claude, Claude Code), puis **Enregistrer**.
4. Quitte complètement Claude et relance-le.

Pour changer d'identifiants plus tard : `Configurer.bat` / `Configurer.command`.

### Mise à jour

Double-clique sur `Mettre a jour.bat` (Windows) ou `Mettre a jour.command`
(macOS), puis relance Claude. Tes identifiants sont conservés.

### Désinstallation

Quitte complètement Claude, puis double-clique sur `Desinstaller.bat`
(Windows) ou `Desinstaller.command` (macOS). ImagePME est retiré de Claude
et le dossier du projet est supprimé, identifiants compris.

### Variante : faire installer ImagePME par Claude

Au lieu des étapes 1 à 3 ci-dessus, tu peux coller ce texte dans
**Claude Code** (onglet *Code* de l'application Claude). Ça ne fonctionne
pas dans l'onglet *Chat* ou *Cowork* : Claude y travaille dans un
environnement isolé qui ne peut pas installer de logiciel sur ton poste.

Si tu as déjà téléchargé ou installé le projet, Claude le réutilise au
lieu de tout réinstaller :

```text
Installe pour moi le serveur MCP ImagePME (https://github.com/BorisSAUVAGE/mcp-imagepme).
0. Avant tout, vérifie que tu peux exécuter des commandes directement sur mon ordinateur (pas dans une machine virtuelle ou un environnement Linux isolé) : sous Windows, la commande "powershell -Command $PSVersionTable" doit fonctionner. Si ce n'est pas le cas, ne télécharge rien : dis-moi de coller ce texte dans l'onglet Code de l'application Claude (Claude Code), ou d'utiliser Installer.bat / Installer.command.
1. Demande-moi d'abord si j'ai déjà téléchargé le projet et, si oui, dans quel dossier. Sinon, télécharge-le (git clone, ou l'archive ZIP de la branche main si git est absent) dans un dossier "mcp-imagepme" de mon dossier personnel.
2. Si ce dossier contient déjà une installation (.venv/bin/imagepme-mcp sur macOS/Linux, .venv\Scripts\imagepme-mcp.exe sur Windows), ne réinstalle rien : lance seulement la fenêtre de configuration avec le Python de .venv (scripts/configure.py). Sinon, lance le script d'installation : install.sh sur macOS/Linux, install.ps1 (powershell -ExecutionPolicy Bypass -File install.ps1) sur Windows. Si Python 3.10+ manque, dis-moi comment l'installer.
3. Une fenêtre va s'ouvrir pour que je saisisse moi-même mes identifiants Comptexpert : ne me les demande jamais dans la conversation.
4. Vérifie ensuite que le serveur "imagepme" est bien déclaré dans la configuration de Claude Desktop (claude_desktop_config.json, clé mcpServers) et dans Claude Code (claude mcp get imagepme), puis dis-moi de quitter complètement Claude et de le relancer.
```

### Installation manuelle

<details>
<summary>Détail des étapes effectuées par le script, si tu préfères les faire toi-même</summary>

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate

pip install -e .
playwright install chromium

cp .env.example .env
# édite .env et renseigne COMPTEXPERT_USERNAME / COMPTEXPERT_PASSWORD

claude mcp add imagepme -- "$(pwd)/.venv/bin/imagepme-mcp"
```

`.env` n'est jamais commité (voir `.gitignore`) et n'est lu que localement
par le serveur pour se connecter en ton nom.

Si `claude mcp add` ne fonctionne pas : copie `.mcp.json.example` en
`.mcp.json` à la racine du projet et remplace le chemin par le chemin
absolu réel de `.venv/bin/imagepme-mcp` (ou `.venv\Scripts\imagepme-mcp.exe`
sur Windows) sur ta machine.

</details>

## Utilisation

Une fois connecté, demande simplement en langage naturel, par exemple :

> Donne-moi les indicateurs TVA de mai 2026, tous secteurs, au national.

> Indicateurs TDFC pour le secteur de la construction en Bretagne, en PDF.

Deux tools sont exposés, chacun avec un paramètre `format` (`"excel"` par
défaut, ou `"pdf"`) :

- **`get_indicateurs_tva`** — indicateurs TVA (ICA/ICAC), mensuels ou
  trimestriels : `periodicite`, `annee`, `periode`, `niveau_sectoriel`,
  `secteur`, `niveau_geo`, `territoire`, `format`.
- **`get_indicateurs_tdfc`** — indicateurs TDFC (données fiscales
  annuelles) : `tranche_ca`, `niveau_sectoriel`, `secteur`, `niveau_geo`,
  `territoire`, `format`.

Chaque appel retourne le chemin local du fichier téléchargé (dans
`.data/downloads/`).

Si les filtres demandés portent sur un échantillon trop restreint, ImagePME
refuse d'afficher un résultat (secret statistique, en général moins de 10
entreprises) : le tool renvoie alors une erreur explicite plutôt qu'un
fichier, en te suggérant d'élargir le niveau géographique ou sectoriel.

## Fonctionnement interne

- La connexion passe par le SSO CAS de l'Ordre (`identification.experts-comptables.org`).
- La session est persistée dans `.data/storage_state.json` pour éviter de
  se reconnecter à chaque appel ; elle est automatiquement renouvelée si
  elle expire.
- Le formulaire réel est une app Plotly Dash embarquée en iframe
  cross-origin — Playwright y accède nativement (contrairement à du code
  JS classique, bloqué par la same-origin policy).

Pour déboguer un sélecteur qui ne matche plus (le site peut évoluer) :

```bash
MCP_IMAGEPME_HEADED=1 python scripts/manual_test.py
```

Ça ouvre un vrai navigateur visible pour observer le flux pas à pas.

## Ajouter un nouveau rapport ImagePME

1. Crée `src/mcp_imagepme/reports/<nom>.py` sur le modèle de `tva.py` ou
   `tdfc.py`, en réutilisant les helpers de `dash_form.py` et
   `reports/base.py`.
2. Expose une fonction `async def` correspondante dans `server.py` avec
   `@mcp.tool()`, en déportant l'appel Playwright (synchrone) via
   `asyncio.to_thread(...)`.

## Avertissement

Ce projet automatise l'accès à un service tiers avec authentification
personnelle. Utilise-le uniquement avec ton propre compte, dans le respect
des conditions d'utilisation d'ImagePME et de l'Ordre des
experts-comptables.
