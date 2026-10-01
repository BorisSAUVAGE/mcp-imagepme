import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / ".data"
DOWNLOAD_DIR = DATA_DIR / "downloads"
STORAGE_STATE_PATH = DATA_DIR / "storage_state.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

COMPTEXPERT_USERNAME = os.environ.get("COMPTEXPERT_USERNAME")
COMPTEXPERT_PASSWORD = os.environ.get("COMPTEXPERT_PASSWORD")

IMAGEPME_DONNEES_URL = "https://www.imagepme.fr/donnees"

# Headless par défaut ; passer MCP_IMAGEPME_HEADED=1 pour observer le
# navigateur pendant la mise au point des sélecteurs.
HEADED = os.environ.get("MCP_IMAGEPME_HEADED") == "1"
