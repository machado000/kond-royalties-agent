"""Servicos reutilizaveis para CLI e MCP."""

from __future__ import annotations

from mcp_server.catalog import build_catalog_payload
from mcp_server.dsu_analytics import get_dsu_booking_quality, get_dsu_missed_opportunities
from mcp_server.models import RoyaltyQueryRequest
from mcp_server.planner import plan_royalty_query
from mcp_server.postgres import describe_schema, list_accessible_schemas
from mcp_server.query_runner import run_royalty_query
from mcp_server.responder import ask_royalties
from mcp_server.settings import load_app_settings, load_postgres_source_config


def get_catalog_payload() -> dict[str, object]:
    return build_catalog_payload()


def get_config_payload() -> dict[str, object]:
    settings = load_app_settings()
    source_config = load_postgres_source_config()
    return {
        "env": {
            **settings.model_dump(),
            "openai_api_key": "***redacted***" if settings.openai_api_key else None,
            "database_url": "***redacted***" if settings.database_url else None,
            "pg_password": "***redacted***" if settings.pg_password else None,
        },
        "sources": source_config.model_dump(),
    }


def get_postgres_diagnostics_payload() -> tuple[int, dict[str, object]]:
    settings = load_app_settings()
    source_config = load_postgres_source_config()
    enabled = settings.postgres_schemas or source_config.schemas

    try:
        schemas = list_accessible_schemas(settings)
    except Exception as exc:
        return 1, {
            "enabled_schemas": enabled,
            "status": "error",
            "error": str(exc),
        }

    return 0, {
        "enabled_schemas": enabled,
        "accessible_schemas": schemas,
        "missing_enabled_schemas": [schema for schema in enabled if schema not in schemas],
        "status": "ok",
    }


def get_schema_payload(schema: str | None) -> tuple[int, dict[str, object]]:
    settings = load_app_settings()
    try:
        tables = describe_schema(settings, schema=schema)
    except Exception as exc:
        return 1, {
            "status": "error",
            "schema": schema,
            "error": str(exc),
        }

    return 0, {
        "status": "ok",
        "schema": schema,
        "tables": tables,
    }


def get_plan_payload(question: str, limit: int, source: str | None = None) -> dict[str, object]:
    request = RoyaltyQueryRequest(question=question, limit=limit, source=source)
    plan = plan_royalty_query(request)
    return plan.model_dump()


def get_run_query_payload(question: str, limit: int, source: str | None = None) -> tuple[int, dict[str, object]]:
    request = RoyaltyQueryRequest(question=question, limit=limit, source=source)
    try:
        plan, result = run_royalty_query(request)
    except Exception as exc:
        return 1, {
            "status": "error",
            "question": question,
            "error": str(exc),
        }

    return 0, {
        "status": "ok",
        "plan": plan.model_dump(),
        "result": result.model_dump(),
    }


def get_dsu_booking_quality_payload(artist: str | None = None) -> tuple[int, dict[str, object]]:
    try:
        result = get_dsu_booking_quality(artist=artist)
    except Exception as exc:
        return 1, {"status": "error", "artist": artist, "error": str(exc)}

    return 0, {"status": "ok", "result": result.model_dump()}


def get_dsu_missed_opportunities_payload(
    artist: str | None = None, lookahead_days: int = 90
) -> tuple[int, dict[str, object]]:
    try:
        result = get_dsu_missed_opportunities(artist=artist, lookahead_days=lookahead_days)
    except Exception as exc:
        return 1, {"status": "error", "artist": artist, "error": str(exc)}

    return 0, {"status": "ok", "result": result.model_dump()}


def get_ask_payload(question: str, limit: int, source: str | None = None) -> tuple[int, dict[str, object]]:
    request = RoyaltyQueryRequest(question=question, limit=limit, source=source)
    try:
        plan, answer = ask_royalties(request)
    except Exception as exc:
        return 1, {
            "status": "error",
            "question": question,
            "error": str(exc),
        }

    return 0, {
        "status": "ok",
        "plan": plan.model_dump(),
        "answer": answer.model_dump(),
    }
