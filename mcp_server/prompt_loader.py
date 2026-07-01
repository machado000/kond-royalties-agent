"""Leitura de prompts locais do agente."""

from __future__ import annotations

from pathlib import Path

from mcp_server.settings import ROOT_DIR


def load_system_prompt() -> str:
    path = ROOT_DIR / "prompts" / "system_pt_br.md"
    return path.read_text(encoding="utf-8").strip()
