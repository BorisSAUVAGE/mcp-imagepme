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

## Installation

Prérequis : [Python 3.10+](https://www.python.org/downloads/) et
[Claude Code](https://claude.com/claude-code) (ou un autre client MCP).

### Installation automatique (recommandé)

```bash
git clone https://github.com/BorisSAUVAGE/mcp-imagepme
cd mcp-imagepme
```

**macOS / Linux :**

```bash
./install.sh
```

**Windows (PowerShell) :**

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1
```

Le script crée l'environnement virtuel, installe les dépendances et
Chromium (pour Playwright), te demande tes identifiants Comptexpert (ou
laisse `.env` à compléter plus tard si tu appuies sur Entrée sans rien
taper), puis déclare le serveur auprès de Claude Code s'il est détecté dans
le PATH. Il peut être relancé sans risque (il réutilise ce qui existe déjà).

Redémarre Claude Code (ou reconnecte via `/mcp` dans une session
interactive) : il te demandera d'approuver le nouveau serveur `imagepme` au
premier lancement.

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
