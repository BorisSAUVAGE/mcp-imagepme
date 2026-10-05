"""Met à jour mcp-imagepme depuis GitHub.

- Dossier cloné avec git : `git pull`.
- Sinon (installation depuis l'archive ZIP) : télécharge la dernière version
  de la branche main et remplace les fichiers du projet, en conservant .env,
  .venv et .data.
Les dépendances ne sont réinstallées que si pyproject.toml a changé.
"""

from __future__ import annotations

import hashlib
import io
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ZIP_URL = "https://github.com/BorisSAUVAGE/mcp-imagepme/archive/refs/heads/main.zip"
KEEP = {".env", ".venv", ".data", ".git", ".mcp.json", ".claude"}


def pyproject_hash() -> str:
    return hashlib.sha256((PROJECT_ROOT / "pyproject.toml").read_bytes()).hexdigest()


def version() -> str:
    for line in (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8").splitlines():
        if line.startswith("version"):
            return line.split("=", 1)[1].strip().strip('"')
    return "?"


def update_git() -> None:
    subprocess.run(["git", "pull", "--ff-only"], cwd=PROJECT_ROOT, check=True)


def update_zip() -> None:
    print("Téléchargement de la dernière version…")
    with urllib.request.urlopen(ZIP_URL, timeout=60) as resp:
        archive = zipfile.ZipFile(io.BytesIO(resp.read()))
    prefix = archive.namelist()[0].split("/", 1)[0] + "/"
    for info in archive.infolist():
        rel = info.filename[len(prefix):]
        if not rel or rel.split("/", 1)[0] in KEEP:
            continue
        target = PROJECT_ROOT / rel
        if info.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(info) as src, open(target, "wb") as dst:
            shutil.copyfileobj(src, dst)
        mode = info.external_attr >> 16
        if mode & 0o111:
            target.chmod(target.stat().st_mode | 0o755)


def main() -> int:
    before_hash, before_version = pyproject_hash(), version()
    try:
        if (PROJECT_ROOT / ".git").is_dir() and shutil.which("git"):
            update_git()
        else:
            update_zip()
    except Exception as e:  # noqa: BLE001
        print(f"Échec de la mise à jour : {e}")
        return 1

    if pyproject_hash() != before_hash:
        print("Mise à jour des dépendances…")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-e", ".", "-q"],
                           cwd=PROJECT_ROOT, check=True)
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"],
                           cwd=PROJECT_ROOT, check=True)
        except subprocess.CalledProcessError:
            print("Échec de l'installation des dépendances. Quitte complètement Claude puis relance la mise à jour.")
            return 1

    after_version = version()
    if after_version != before_version:
        print(f"ImagePME mis à jour : {before_version} → {after_version}.")
    else:
        print(f"ImagePME est à jour (version {after_version}).")
    print("Quitte complètement Claude puis relance-le pour utiliser la nouvelle version.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
