"""Retire mcp-imagepme de Claude Desktop, de Claude Code et de Codex.

La suppression du dossier du projet (avec .env et .venv) est faite ensuite
par Desinstaller.bat / Desinstaller.command, une fois ce script terminé :
sous Windows, le Python de .venv ne peut pas effacer son propre dossier.
"""

from __future__ import annotations

import json
import shutil
import subprocess

from configure import PROJECT_ROOT, SERVER_NAME, claude_cli, desktop_config_paths, unregister_codex


def unregister_desktop() -> None:
    for path in desktop_config_paths():
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8").strip()
        config = json.loads(text) if text else {}
        servers = config.get("mcpServers", {})
        if SERVER_NAME not in servers:
            continue
        shutil.copy2(path, path.with_suffix(".json.bak"))
        del servers[SERVER_NAME]
        if not servers:
            del config["mcpServers"]
        path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Retiré de Claude Desktop ({path}).")


def unregister_code() -> None:
    cli = claude_cli()
    if not cli:
        return
    for scope in ("local", "user"):
        result = subprocess.run([cli, "mcp", "remove", SERVER_NAME, "-s", scope],
                                cwd=PROJECT_ROOT, capture_output=True)
        if result.returncode == 0:
            print(f"Retiré de Claude Code (portée {scope}).")


if __name__ == "__main__":
    try:
        unregister_desktop()
    except Exception as e:  # noqa: BLE001
        print(f"Échec Claude Desktop : {e}")
    unregister_code()
    try:
        if unregister_codex():
            print("Retiré de Codex.")
    except Exception as e:  # noqa: BLE001
        print(f"Échec Codex : {e}")
