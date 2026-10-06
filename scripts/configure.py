"""Fenêtre de configuration de mcp-imagepme.

Demande les identifiants Comptexpert (enregistrés dans .env) puis déclare le
serveur auprès de Claude Desktop (onglet Chat) et de Claude Code.
Lancé automatiquement par l'installeur ; peut être relancé à tout moment
pour changer d'identifiants : `Configurer` (.bat / .command).
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
REPO_URL = "https://github.com/BorisSAUVAGE/mcp-imagepme"
SERVER_NAME = "imagepme"

IS_WINDOWS = platform.system() == "Windows"
SERVER_EXE = PROJECT_ROOT / ".venv" / ("Scripts/imagepme-mcp.exe" if IS_WINDOWS else "bin/imagepme-mcp")

INSTALL_PROMPT = f"""\
Installe pour moi le serveur MCP ImagePME ({REPO_URL}).
0. Avant tout, vérifie que tu peux exécuter des commandes directement sur mon ordinateur (pas dans une machine virtuelle ou un environnement Linux isolé) : sous Windows, la commande "powershell -Command $PSVersionTable" doit fonctionner. Si ce n'est pas le cas, ne télécharge rien : dis-moi de coller ce texte dans l'onglet Code de l'application Claude (Claude Code), ou d'utiliser Installer.bat / Installer.command.
1. Demande-moi d'abord si j'ai déjà téléchargé le projet et, si oui, dans quel dossier. Sinon, télécharge-le (git clone, ou l'archive ZIP de la branche main si git est absent) dans un dossier "mcp-imagepme" de mon dossier personnel.
2. Si ce dossier contient déjà une installation (.venv/bin/imagepme-mcp sur macOS/Linux, .venv\\Scripts\\imagepme-mcp.exe sur Windows), ne réinstalle rien : lance seulement la fenêtre de configuration avec le Python de .venv (scripts/configure.py). Sinon, lance le script d'installation : install.sh sur macOS/Linux, install.ps1 (powershell -ExecutionPolicy Bypass -File install.ps1) sur Windows. Si Python 3.10+ manque, dis-moi comment l'installer.
3. Une fenêtre va s'ouvrir pour que je saisisse moi-même mes identifiants Comptexpert : ne me les demande jamais dans la conversation.
4. Vérifie ensuite que le serveur "{SERVER_NAME}" est bien déclaré dans la configuration de Claude Desktop (claude_desktop_config.json, clé mcpServers) et dans Claude Code (claude mcp get {SERVER_NAME}), puis dis-moi de quitter complètement Claude et de le relancer.
"""


# --- .env -------------------------------------------------------------------

def read_env() -> dict[str, str]:
    if not ENV_PATH.exists():
        return {}
    try:
        from dotenv import dotenv_values
        return {k: v or "" for k, v in dotenv_values(ENV_PATH).items()}
    except ImportError:
        return {}


def _quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def write_env(username: str, password: str) -> None:
    lines = ENV_PATH.read_text(encoding="utf-8").splitlines() if ENV_PATH.exists() else []
    values = {"COMPTEXPERT_USERNAME": username, "COMPTEXPERT_PASSWORD": password}
    out = []
    for line in lines:
        key = line.split("=", 1)[0].strip()
        if key in values:
            out.append(f"{key}={_quote(values.pop(key))}")
        else:
            out.append(line)
    out += [f"{k}={_quote(v)}" for k, v in values.items()]
    ENV_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")
    if not IS_WINDOWS:
        ENV_PATH.chmod(0o600)


# --- Claude Desktop ---------------------------------------------------------

def desktop_config_paths() -> list[Path]:
    home = Path.home()
    system = platform.system()
    if system == "Darwin":
        return [home / "Library/Application Support/Claude/claude_desktop_config.json"]
    if IS_WINDOWS:
        paths = [Path(os.environ.get("APPDATA", home / "AppData/Roaming")) / "Claude/claude_desktop_config.json"]
        # Version Microsoft Store (MSIX) : configuration virtualisée ailleurs.
        packages = Path(os.environ.get("LOCALAPPDATA", home / "AppData/Local")) / "Packages"
        if packages.is_dir():
            for pkg in packages.glob("Claude_*"):
                paths.append(pkg / "LocalCache/Roaming/Claude/claude_desktop_config.json")
        return paths
    return [home / ".config/Claude/claude_desktop_config.json"]


def register_desktop() -> list[Path]:
    done = []
    for path in desktop_config_paths():
        config = {}
        if path.exists():
            text = path.read_text(encoding="utf-8").strip()
            config = json.loads(text) if text else {}
            shutil.copy2(path, path.with_suffix(".json.bak"))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
        config.setdefault("mcpServers", {})[SERVER_NAME] = {"command": str(SERVER_EXE)}
        path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
        done.append(path)
    return done


# --- Claude Code ------------------------------------------------------------

def claude_cli() -> str | None:
    return shutil.which("claude")


def register_code() -> None:
    cli = claude_cli()
    if not cli:
        raise RuntimeError("commande 'claude' introuvable")
    for scope in ("local", "user"):
        subprocess.run([cli, "mcp", "remove", SERVER_NAME, "-s", scope],
                       cwd=PROJECT_ROOT, capture_output=True)
    result = subprocess.run([cli, "mcp", "add", "-s", "user", SERVER_NAME, "--", str(SERVER_EXE)],
                            cwd=PROJECT_ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())


# --- Codex (OpenAI) ---------------------------------------------------------

CODEX_SECTION = f"[mcp_servers.{SERVER_NAME}]"


def codex_config_path() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "config.toml"


def codex_detected() -> bool:
    return shutil.which("codex") is not None or codex_config_path().parent.is_dir()


def _without_codex_section(text: str) -> list[str]:
    """Lignes de config.toml sans la section [mcp_servers.imagepme] (ni ses
    sous-tables, ex. [mcp_servers.imagepme.env])."""
    out, skipping = [], False
    for line in text.splitlines():
        header = line.strip()
        if header.startswith("["):
            skipping = header == CODEX_SECTION or header.startswith(CODEX_SECTION[:-1] + ".")
        if not skipping:
            out.append(line)
    while out and not out[-1].strip():
        out.pop()
    return out


def register_codex() -> Path:
    path = codex_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    if path.exists():
        shutil.copy2(path, path.with_suffix(".toml.bak"))
        lines = _without_codex_section(path.read_text(encoding="utf-8"))
    # Chaîne littérale TOML ('...') : pas d'échappement des \ des chemins Windows.
    lines += ["", CODEX_SECTION, f"command = '{SERVER_EXE}'", ""]
    path.write_text("\n".join(lines).lstrip("\n"), encoding="utf-8")
    return path


def unregister_codex() -> bool:
    path = codex_config_path()
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    if CODEX_SECTION not in text:
        return False
    shutil.copy2(path, path.with_suffix(".toml.bak"))
    path.write_text("\n".join(_without_codex_section(text)) + "\n", encoding="utf-8")
    return True


def apply(username: str, password: str, desktop: bool, code: bool, codex: bool = False) -> list[str]:
    report = []
    if username:
        write_env(username, password)
        report.append("Identifiants enregistrés.")
    if desktop:
        try:
            for p in register_desktop():
                report.append(f"Claude Desktop configuré ({p}).")
        except Exception as e:  # noqa: BLE001
            report.append(f"Échec Claude Desktop : {e}")
    if code:
        try:
            register_code()
            report.append("Claude Code configuré.")
        except Exception as e:  # noqa: BLE001
            report.append(f"Échec Claude Code : {e}")
    if codex:
        try:
            report.append(f"Codex configuré ({register_codex()}).")
        except Exception as e:  # noqa: BLE001
            report.append(f"Échec Codex : {e}")
    return report


# --- Interface --------------------------------------------------------------

def run_gui() -> None:
    import tkinter as tk
    from tkinter import messagebox, ttk

    env = read_env()
    root = tk.Tk()
    root.title("ImagePME pour Claude")
    root.resizable(False, False)
    frame = ttk.Frame(root, padding=20)
    frame.grid()

    ttk.Label(frame, text="Identifiants Comptexpert", font=("", 14, "bold")).grid(columnspan=2, sticky="w")
    ttk.Label(frame, text="Ils restent sur cet ordinateur (fichier .env), jamais envoyés à Claude.",
              foreground="gray").grid(columnspan=2, sticky="w", pady=(0, 12))

    user_var = tk.StringVar(value=env.get("COMPTEXPERT_USERNAME", ""))
    pass_var = tk.StringVar(value=env.get("COMPTEXPERT_PASSWORD", ""))
    ttk.Label(frame, text="Identifiant").grid(row=2, column=0, sticky="w")
    user_entry = ttk.Entry(frame, textvariable=user_var, width=36)
    user_entry.grid(row=2, column=1, pady=3)
    ttk.Label(frame, text="Mot de passe").grid(row=3, column=0, sticky="w")
    pass_entry = ttk.Entry(frame, textvariable=pass_var, width=36, show="•")
    pass_entry.grid(row=3, column=1, pady=3)
    show_var = tk.BooleanVar()
    ttk.Checkbutton(frame, text="Afficher", variable=show_var,
                    command=lambda: pass_entry.config(show="" if show_var.get() else "•")
                    ).grid(row=4, column=1, sticky="w")

    ttk.Label(frame, text="Activer ImagePME dans", font=("", 12, "bold")).grid(row=5, columnspan=2, sticky="w", pady=(14, 4))
    desktop_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(frame, text="Claude (application, onglet Chat)", variable=desktop_var).grid(row=6, columnspan=2, sticky="w")
    has_cli = claude_cli() is not None
    code_var = tk.BooleanVar(value=has_cli)
    ttk.Checkbutton(frame, text="Claude Code" + ("" if has_cli else " (non détecté)"), variable=code_var,
                    state="normal" if has_cli else "disabled").grid(row=7, columnspan=2, sticky="w")
    has_codex = codex_detected()
    codex_var = tk.BooleanVar(value=has_codex)
    ttk.Checkbutton(frame, text="Codex (OpenAI)" + ("" if has_codex else " (non détecté)"), variable=codex_var,
                    state="normal" if has_codex else "disabled").grid(row=8, columnspan=2, sticky="w")

    def save() -> None:
        user, pwd = user_var.get().strip(), pass_var.get()
        if not user or not pwd:
            if not messagebox.askyesno("Identifiants manquants",
                                       "Aucun identifiant saisi. Continuer quand même ?"):
                return
        report = apply(user, pwd, desktop_var.get(), code_var.get(), codex_var.get())
        report.append("\nQuitte complètement Claude puis relance-le pour activer ImagePME.")
        ok = not any(r.startswith("Échec") for r in report)
        (messagebox.showinfo if ok else messagebox.showwarning)("ImagePME", "\n".join(report))
        if ok:
            root.destroy()

    buttons = ttk.Frame(frame)
    buttons.grid(row=9, columnspan=2, pady=(18, 0), sticky="ew")
    ttk.Button(buttons, text="Enregistrer", command=save).pack(side="right")
    ttk.Button(buttons, text="Annuler", command=root.destroy).pack(side="right", padx=6)

    root.bind("<Return>", lambda _e: save())
    (pass_entry if user_var.get() else user_entry).focus_set()
    root.lift()
    root.attributes("-topmost", True)
    root.after(500, lambda: root.attributes("-topmost", False))
    root.mainloop()


def run_terminal() -> None:
    import getpass

    print("Identifiants Comptexpert (Entrée pour ignorer) :")
    user = input("  Identifiant : ").strip()
    pwd = getpass.getpass("  Mot de passe : ") if user else ""
    for line in apply(user, pwd, desktop=True, code=claude_cli() is not None, codex=codex_detected()):
        print(line)
    print("Quitte complètement Claude puis relance-le pour activer ImagePME.")


def main() -> None:
    if "--prompt" in sys.argv:
        print(INSTALL_PROMPT)
        return
    try:
        import tkinter
    except ImportError:
        run_terminal()
        return
    try:
        run_gui()
    except tkinter.TclError:  # pas d'affichage graphique disponible
        run_terminal()


if __name__ == "__main__":
    main()
