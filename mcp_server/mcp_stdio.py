"""Servidor MCP por stdio, sem dependencia externa."""

from __future__ import annotations

import json
import sys
from typing import Any

from mcp_server.service import (
    get_ask_payload,
    get_catalog_payload,
    get_config_payload,
    get_plan_payload,
    get_postgres_diagnostics_payload,
    get_run_query_payload,
    get_schema_payload,
)


PROTOCOL_VERSION = "2025-06-18"
SERVER_INFO = {
    "name": "kond-royalties-agent",
    "title": "KOND Royalties Agent",
    "version": "0.1.0",
}

TOOLS = [
    {
        "name": "get_royalty_catalog",
        "title": "Royalty Catalog",
        "description": "Retorna metricas, dimensoes e fontes aprovadas do catalogo semantico de royalties.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "get_runtime_config",
        "title": "Runtime Config",
        "description": "Retorna a configuracao efetiva do agente, com segredos redigidos.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "diagnose_postgres_access",
        "title": "Postgres Diagnostics",
        "description": "Valida acesso ao Postgres e schemas habilitados.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "describe_schema",
        "title": "Describe Schema",
        "description": (
            "Introspecta tabelas e colunas reais do Postgres via information_schema. "
            "Use para descobrir o schema real do banco de royalties."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "schema": {"type": "string", "description": "Nome do schema. Se omitido, usa todos os schemas habilitados."},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "plan_royalty_query",
        "title": "Plan Royalty Query",
        "description": "Converte uma pergunta em plano semantico controlado.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "default": 100},
            },
            "required": ["question"],
            "additionalProperties": False,
        },
    },
    {
        "name": "run_royalty_query",
        "title": "Run Royalty Query",
        "description": "Executa consulta controlada no Postgres e retorna plano, SQL e linhas.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "default": 100},
            },
            "required": ["question"],
            "additionalProperties": False,
        },
    },
    {
        "name": "ask_royalties",
        "title": "Ask Royalties",
        "description": "Executa a consulta e devolve resposta executiva em portugues do Brasil.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "default": 100},
            },
            "required": ["question"],
            "additionalProperties": False,
        },
    },
]


def _tool_map() -> dict[str, dict[str, Any]]:
    return {tool["name"]: tool for tool in TOOLS}


def _json_dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _text_result(payload: dict[str, Any], is_error: bool = False) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False, indent=2)}],
        "structuredContent": payload,
        "isError": is_error,
    }


def _handle_initialize(message_id: Any) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": message_id,
        "result": {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {
                "tools": {
                    "listChanged": False,
                }
            },
            "serverInfo": SERVER_INFO,
            "instructions": (
                "Use as tools semanticas para consultar performance de royalties no Postgres. "
                "Respostas devem permanecer em portugues do Brasil."
            ),
        },
    }


def _handle_tools_list(message_id: Any) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": message_id,
        "result": {
            "tools": TOOLS,
        },
    }


def _coerce_limit(arguments: dict[str, Any]) -> int:
    limit = arguments.get("limit", 100)
    if not isinstance(limit, int):
        raise ValueError("`limit` deve ser inteiro.")
    return limit


def _handle_tool_call(message_id: Any, params: dict[str, Any]) -> dict[str, Any]:
    tool_name = params.get("name")
    arguments = params.get("arguments") or {}
    if tool_name not in _tool_map():
        return {
            "jsonrpc": "2.0",
            "id": message_id,
            "error": {"code": -32602, "message": f"Unknown tool: {tool_name}"},
        }

    try:
        if tool_name == "get_royalty_catalog":
            payload = get_catalog_payload()
            result = _text_result(payload)
        elif tool_name == "get_runtime_config":
            payload = get_config_payload()
            result = _text_result(payload)
        elif tool_name == "diagnose_postgres_access":
            _, payload = get_postgres_diagnostics_payload()
            result = _text_result(payload, is_error=payload.get("status") == "error")
        elif tool_name == "describe_schema":
            _, payload = get_schema_payload(schema=arguments.get("schema"))
            result = _text_result(payload, is_error=payload.get("status") == "error")
        elif tool_name == "plan_royalty_query":
            question = arguments["question"]
            payload = get_plan_payload(question=question, limit=_coerce_limit(arguments))
            result = _text_result(payload)
        elif tool_name == "run_royalty_query":
            question = arguments["question"]
            status_code, payload = get_run_query_payload(question=question, limit=_coerce_limit(arguments))
            result = _text_result(payload, is_error=status_code != 0)
        elif tool_name == "ask_royalties":
            question = arguments["question"]
            status_code, payload = get_ask_payload(question=question, limit=_coerce_limit(arguments))
            result = _text_result(payload, is_error=status_code != 0)
        else:
            raise ValueError(f"Tool sem implementacao: {tool_name}")
    except KeyError as exc:
        return {
            "jsonrpc": "2.0",
            "id": message_id,
            "error": {"code": -32602, "message": f"Parametro obrigatorio ausente: {exc.args[0]}"},
        }
    except Exception as exc:
        result = _text_result({"status": "error", "error": str(exc)}, is_error=True)

    return {"jsonrpc": "2.0", "id": message_id, "result": result}


def handle_message(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    message_id = message.get("id")

    if method == "initialize":
        return _handle_initialize(message_id)
    if method == "notifications/initialized":
        return None
    if method == "ping":
        return {"jsonrpc": "2.0", "id": message_id, "result": {}}
    if method == "tools/list":
        return _handle_tools_list(message_id)
    if method == "tools/call":
        return _handle_tool_call(message_id, message.get("params") or {})

    if message_id is None:
        return None

    return {
        "jsonrpc": "2.0",
        "id": message_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def serve_stdio() -> int:
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            error = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {exc.msg}"},
            }
            sys.stdout.write(_json_dumps(error) + "\n")
            sys.stdout.flush()
            continue

        response = handle_message(message)
        if response is None:
            continue
        sys.stdout.write(_json_dumps(response) + "\n")
        sys.stdout.flush()
    return 0
