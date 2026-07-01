"""Instala/atualiza a entrada MCP do kond-royalties-agent na configuracao de um cliente.

Uso:
  python scripts/install_mcp_config.py --client antigravity
  python scripts/install_mcp_config.py --client claude-desktop
  python scripts/install_mcp_config.py --client claude-desktop --dry-run

Faz merge da entrada `kond_royalties` na configuracao existente do cliente
(sem apagar outros servidores ja configurados), usando o caminho absoluto
deste repositorio e do seu `.venv`.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON_BIN = REPO_ROOT / ".venv" / ("Scripts/python.exe" if platform.system() == "Windows" else "bin/python")

SERVER_NAME = "kond_royalties"

CLIENT_CONFIG_PATHS = {
    "antigravity": Path.home() / ".gemini" / "config" / "mcp_config.json",
    "claude-desktop": (
        Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
        if platform.system() == "Windows"
        else Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    ),
}


def build_entry(client: str) -> dict[str, object]:
    entry: dict[str, object] = {
        "command": str(PYTHON_BIN),
        "args": ["-m", "mcp_server.server", "serve-mcp"],
    }
    if client == "antigravity":
        entry["cwd"] = str(REPO_ROOT)
    return entry


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", required=True, choices=sorted(CLIENT_CONFIG_PATHS))
    parser.add_argument("--dry-run", action="store_true", help="Mostra o resultado sem escrever o arquivo.")
    args = parser.parse_args()

    if not PYTHON_BIN.exists():
        print(
            f"Aviso: {PYTHON_BIN} nao existe ainda. Crie o venv e rode "
            "'pip install -e \".[dev]\"' antes de usar este servidor.",
            file=sys.stderr,
        )

    config_path = CLIENT_CONFIG_PATHS[args.client]
    config: dict[str, object] = {}
    if config_path.exists():
        raw = config_path.read_text(encoding="utf-8").strip()
        config = json.loads(raw) if raw else {}

    config.setdefault("mcpServers", {})
    config["mcpServers"][SERVER_NAME] = build_entry(args.client)

    output = json.dumps(config, indent=2, ensure_ascii=False) + "\n"

    if args.dry_run:
        print(output, end="")
        return

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(output, encoding="utf-8")
    print(f"Atualizado: {config_path}")


if __name__ == "__main__":
    main()
