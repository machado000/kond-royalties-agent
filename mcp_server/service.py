"""Servicos reutilizaveis para CLI e MCP."""

from __future__ import annotations

from mcp_server.bigquery import list_accessible_datasets
from mcp_server.catalog import build_catalog_payload
from mcp_server.models import MarketingQueryRequest
from mcp_server.planner import plan_marketing_query
from mcp_server.query_runner import run_marketing_query
from mcp_server.responder import ask_marketing
from mcp_server.settings import load_app_settings, load_bigquery_source_config


def get_catalog_payload() -> dict[str, object]:
    return build_catalog_payload()


def get_config_payload() -> dict[str, object]:
    settings = load_app_settings()
    source_config = load_bigquery_source_config()
    return {
        "env": {
            **settings.model_dump(),
            "openai_api_key": "***redacted***" if settings.openai_api_key else None,
        },
        "sources": source_config.model_dump(),
    }


def get_bigquery_diagnostics_payload() -> tuple[int, dict[str, object]]:
    settings = load_app_settings()
    source_config = load_bigquery_source_config()
    enabled = settings.bigquery_datasets or source_config.datasets

    try:
        datasets = list_accessible_datasets(settings)
    except Exception as exc:
        return 1, {
            "project_id": settings.bigquery_project_id or source_config.project_id,
            "enabled_datasets": enabled,
            "status": "error",
            "error": str(exc),
        }

    return 0, {
        "project_id": settings.bigquery_project_id or source_config.project_id,
        "enabled_datasets": enabled,
        "accessible_datasets": datasets,
        "missing_enabled_datasets": [dataset for dataset in enabled if dataset not in datasets],
        "status": "ok",
    }


def get_plan_payload(question: str, limit: int) -> dict[str, object]:
    request = MarketingQueryRequest(question=question, limit=limit)
    plan = plan_marketing_query(request)
    return plan.model_dump()


def get_run_query_payload(question: str, limit: int) -> tuple[int, dict[str, object]]:
    request = MarketingQueryRequest(question=question, limit=limit)
    try:
        plan, result = run_marketing_query(request)
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


def get_ask_payload(question: str, limit: int) -> tuple[int, dict[str, object]]:
    request = MarketingQueryRequest(question=question, limit=limit)
    try:
        plan, answer = ask_marketing(request)
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
