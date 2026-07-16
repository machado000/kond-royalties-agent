"""Entrypoint do servidor MCP."""

from __future__ import annotations

import argparse
import json
import os

from mcp_server.mcp_stdio import serve_stdio
from mcp_server.service import (
    get_ask_payload,
    get_catalog_payload,
    get_config_payload,
    get_plan_payload,
    get_postgres_diagnostics_payload,
    get_run_query_payload,
    get_schema_payload,
)


def _emit(payload: dict[str, object]) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kond-royalties-mcp")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("catalog", help="Exibe o catalogo semantico.")
    subparsers.add_parser("config", help="Exibe configuracoes efetivas.")
    subparsers.add_parser("diagnose-postgres", help="Valida acesso e schemas do Postgres.")
    schema_parser = subparsers.add_parser(
        "describe-schema", help="Introspecta tabelas e colunas reais via information_schema."
    )
    schema_parser.add_argument("--schema", default=None, help="Schema especifico. Se omitido, usa todos os habilitados.")
    subparsers.add_parser("serve-mcp", help="Inicia o servidor MCP por stdio.")
    subparsers.add_parser("serve-http", help="Inicia o servidor MCP via Streamable HTTP.")
    plan_parser = subparsers.add_parser("plan-query", help="Planeja uma consulta sem executa-la.")
    plan_parser.add_argument("--question", required=True)
    plan_parser.add_argument("--limit", type=int, default=100)
    run_parser = subparsers.add_parser("run-query", help="Executa uma consulta de royalties no Postgres.")
    run_parser.add_argument("--question", required=True)
    run_parser.add_argument("--limit", type=int, default=100)
    ask_parser = subparsers.add_parser("ask", help="Executa a consulta e devolve resposta executiva.")
    ask_parser.add_argument("--question", required=True)
    ask_parser.add_argument("--limit", type=int, default=100)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "catalog":
        raise SystemExit(_emit(get_catalog_payload()))
    if args.command == "config":
        raise SystemExit(_emit(get_config_payload()))
    if args.command == "diagnose-postgres":
        status_code, payload = get_postgres_diagnostics_payload()
        _emit(payload)
        raise SystemExit(status_code)
    if args.command == "describe-schema":
        status_code, payload = get_schema_payload(schema=args.schema)
        _emit(payload)
        raise SystemExit(status_code)
    if args.command == "serve-mcp":
        raise SystemExit(serve_stdio())
    if args.command == "serve-http":
        from mcp_server.mcp_http import run_http  # lazy: mantem `mcp` opcional

        port = int(os.environ.get("PORT", "8080"))
        raise SystemExit(run_http(host="0.0.0.0", port=port))
    if args.command == "plan-query":
        raise SystemExit(_emit(get_plan_payload(args.question, args.limit)))
    if args.command == "run-query":
        status_code, payload = get_run_query_payload(args.question, args.limit)
        _emit(payload)
        raise SystemExit(status_code)
    if args.command == "ask":
        status_code, payload = get_ask_payload(args.question, args.limit)
        _emit(payload)
        raise SystemExit(status_code)

    raise SystemExit(f"Comando desconhecido: {args.command}")


if __name__ == "__main__":
    main()
