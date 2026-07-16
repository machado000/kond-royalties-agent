"""Servidor MCP via Streamable HTTP, para hospedagem compartilhada.

Transporte adicional ao stdio (mcp_stdio.py) — reutiliza as mesmas funcoes
de negocio em mcp_server.service. Requer o extra opcional `http`
(pip install ".[http]"), nao usado pelo caminho stdio local.
"""

from __future__ import annotations

import json
import os
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.server.transport_security import TransportSecuritySettings

from mcp_server.service import (
    get_ask_payload,
    get_catalog_payload,
    get_config_payload,
    get_plan_payload,
    get_postgres_diagnostics_payload,
    get_run_query_payload,
    get_schema_payload,
)


INSTRUCTIONS = (
    "Use as tools semanticas para consultar performance de royalties no Postgres. "
    "Respostas devem permanecer em portugues do Brasil."
)

mcp = FastMCP(name="kond-royalties-agent", instructions=INSTRUCTIONS)


def _catalog_tool() -> dict[str, Any]:
    return get_catalog_payload()


def _config_tool() -> dict[str, Any]:
    return get_config_payload()


def _diagnose_tool() -> dict[str, Any]:
    status_code, payload = get_postgres_diagnostics_payload()
    if status_code != 0:
        raise ToolError(json.dumps(payload, ensure_ascii=False))
    return payload


def _describe_schema_tool(schema: str | None = None) -> dict[str, Any]:
    status_code, payload = get_schema_payload(schema=schema)
    if status_code != 0:
        raise ToolError(json.dumps(payload, ensure_ascii=False))
    return payload


def _plan_tool(question: str, limit: int = 100) -> dict[str, Any]:
    return get_plan_payload(question=question, limit=limit)


def _run_query_tool(question: str, limit: int = 100) -> dict[str, Any]:
    status_code, payload = get_run_query_payload(question=question, limit=limit)
    if status_code != 0:
        raise ToolError(json.dumps(payload, ensure_ascii=False))
    return payload


def _ask_tool(question: str, limit: int = 100) -> dict[str, Any]:
    status_code, payload = get_ask_payload(question=question, limit=limit)
    if status_code != 0:
        raise ToolError(json.dumps(payload, ensure_ascii=False))
    return payload


mcp.tool(
    name="get_royalty_catalog",
    title="Royalty Catalog",
    description="Retorna metricas, dimensoes e fontes aprovadas do catalogo semantico de royalties.",
)(_catalog_tool)

mcp.tool(
    name="get_runtime_config",
    title="Runtime Config",
    description="Retorna a configuracao efetiva do agente, com segredos redigidos.",
)(_config_tool)

mcp.tool(
    name="diagnose_postgres_access",
    title="Postgres Diagnostics",
    description="Valida acesso ao Postgres e schemas habilitados.",
)(_diagnose_tool)

mcp.tool(
    name="describe_schema",
    title="Describe Schema",
    description=(
        "Introspecta tabelas e colunas reais do Postgres via information_schema. "
        "Use para descobrir o schema real do banco de royalties."
    ),
)(_describe_schema_tool)

mcp.tool(
    name="plan_royalty_query",
    title="Plan Royalty Query",
    description="Converte uma pergunta em plano semantico controlado.",
)(_plan_tool)

mcp.tool(
    name="run_royalty_query",
    title="Run Royalty Query",
    description="Executa consulta controlada no Postgres e retorna plano, SQL e linhas.",
)(_run_query_tool)

mcp.tool(
    name="ask_royalties",
    title="Ask Royalties",
    description="Executa a consulta e devolve resposta executiva em portugues do Brasil.",
)(_ask_tool)


class BearerAuthMiddleware:
    """Middleware ASGI cru (nao Starlette BaseHTTPMiddleware, que lida mal
    com respostas de longa duracao/streaming). Deixa scopes que nao sao
    `http` passarem direto -- crucialmente `lifespan`, que inicia/encerra
    o session manager do FastMCP. Aceita um conjunto de tokens para permitir
    rotacao semanal sem derrubar quem ainda usa o token antigo.
    """

    def __init__(self, app, valid_tokens: set[str]) -> None:
        self.app = app
        self.valid_tokens = valid_tokens

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        auth_header = headers.get(b"authorization", b"").decode("latin-1")
        token = auth_header.removeprefix("Bearer ") if auth_header.startswith("Bearer ") else None

        if token not in self.valid_tokens:
            await send(
                {
                    "type": "http.response.start",
                    "status": 401,
                    "headers": [(b"content-type", b"application/json")],
                }
            )
            await send({"type": "http.response.body", "body": b'{"error": "unauthorized"}'})
            return

        await self.app(scope, receive, send)


def _configure_allowed_hosts() -> None:
    """O SDK `mcp` valida o header Host por padrao (protecao contra DNS
    rebinding) e so libera localhost/127.0.0.1 se nada for configurado --
    isso derruba qualquer request feito para um dominio/IP publico com 421.
    MCP_ALLOWED_HOSTS declara os hosts reais (dominio:porta) usados neste
    deploy, mantendo a protecao ligada em vez de desativa-la.
    """
    raw = os.environ.get("MCP_ALLOWED_HOSTS", "")
    hosts = [h.strip() for h in raw.split(",") if h.strip()]
    if not hosts:
        return
    origins = [f"{scheme}://{host}" for host in hosts for scheme in ("http", "https")]
    mcp.settings.transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=hosts,
        allowed_origins=origins,
    )


def build_asgi_app():
    """Falha fechado: recusa construir o app (derruba o processo antes de
    abrir a porta) se MCP_API_KEYS nao estiver definido -- nunca servir um
    servidor de tools sobre dados de royalties sem autenticacao, silenciosamente.
    """
    raw = os.environ.get("MCP_API_KEYS", "")
    valid_tokens = {token.strip() for token in raw.split(",") if token.strip()}
    if not valid_tokens:
        raise RuntimeError(
            "MCP_API_KEYS deve estar definido (lista separada por virgula) "
            "para iniciar o servidor MCP remoto."
        )
    _configure_allowed_hosts()
    return BearerAuthMiddleware(mcp.streamable_http_app(), valid_tokens=valid_tokens)


def run_http(host: str = "0.0.0.0", port: int = 8080) -> int:
    import uvicorn

    uvicorn.run(build_asgi_app(), host=host, port=port, log_level="info")
    return 0
