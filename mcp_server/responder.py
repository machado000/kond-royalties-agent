"""Sintese executiva de respostas de performance de royalties."""

from __future__ import annotations

import json
from typing import Any

import requests

from mcp_server.models import PlannedQuery, RoyaltyAnswer, RoyaltyQueryRequest, RoyaltyQueryResult
from mcp_server.prompt_loader import load_system_prompt
from mcp_server.query_runner import run_royalty_query
from mcp_server.settings import load_app_settings


def _format_number(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, int):
        return f"{value:,}".replace(",", ".")
    if isinstance(value, float):
        return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return str(value)


def suggest_visual(plan: PlannedQuery) -> str:
    if "period" in plan.dimensions:
        return "linha temporal"
    if "track" in plan.dimensions:
        return "barras por faixa"
    if "artist" in plan.dimensions:
        return "barras por artista"
    if "composer" in plan.dimensions:
        return "barras por compositor"
    if "origem" in plan.dimensions:
        return "barras por origem"
    if "revenue_type" in plan.dimensions:
        return "barras por tipo de receita"
    if "territory" in plan.dimensions:
        return "barras por territorio"
    if "platform" in plan.dimensions:
        return "barras por plataforma"
    return "tabela resumida"


def _top_rows(rows: list[dict[str, Any]], metric: str, limit: int = 3) -> list[dict[str, Any]]:
    def sort_key(item: dict[str, Any]) -> float:
        value = item.get(metric)
        if value is None:
            return float("-inf")
        try:
            return float(value)
        except (TypeError, ValueError):
            return float("-inf")

    return sorted(rows, key=sort_key, reverse=True)[:limit]


def _prepare_llm_rows(plan: PlannedQuery, result: RoyaltyQueryResult) -> list[dict[str, Any]]:
    primary_metric = plan.metrics[0] if plan.metrics else "revenue"
    ranked_rows = _top_rows(result.rows, primary_metric, limit=20)
    meaningful_rows = [
        row
        for row in ranked_rows
        if any((row.get(metric) or 0) not in (0, 0.0) for metric in plan.metrics)
    ]
    return meaningful_rows[:10] or ranked_rows[:10]


def _metric_totals(plan: PlannedQuery, result: RoyaltyQueryResult) -> dict[str, float]:
    totals: dict[str, float] = {}
    for metric in plan.metrics:
        total = 0.0
        for row in result.rows:
            value = row.get(metric)
            if isinstance(value, (int, float)):
                total += float(value)
        totals[metric] = total
    return totals


def build_fallback_answer(plan: PlannedQuery, result: RoyaltyQueryResult) -> RoyaltyAnswer:
    primary_metric = plan.metrics[0] if plan.metrics else "revenue"
    top_rows = _top_rows(result.rows, primary_metric)

    if not result.rows:
        answer_markdown = (
            "Nao encontrei linhas para o recorte solicitado. "
            "Vale revisar o periodo, os filtros ou a disponibilidade de dados nas fontes conectadas."
        )
        summary = "Consulta sem linhas no periodo solicitado."
    else:
        dimension = plan.dimensions[0] if plan.dimensions else "agrupamento"
        bullets = []
        for row in top_rows:
            label = row.get(dimension, "(sem valor)")
            parts = [f"**{label}**"]
            for metric in plan.metrics:
                parts.append(f"{metric}: {_format_number(row.get(metric))}")
            bullets.append("- " + " | ".join(parts))
        answer_markdown = "\n".join(
            [
                f"Analisei `{', '.join(plan.metrics)}` por `{', '.join(plan.dimensions)}`.",
                "",
                "Principais linhas:",
                *bullets,
            ]
        )
        top_label = top_rows[0].get(dimension, "(sem valor)")
        top_value = _format_number(top_rows[0].get(primary_metric))
        summary = f"{top_label} lidera em {primary_metric} com {top_value}."

    followups = [
        "Abrir a analise por origem ou tipo de receita.",
        "Comparar com o periodo anterior.",
        "Gerar relatorio executivo em PDF.",
    ]
    return RoyaltyAnswer(
        answer_markdown=answer_markdown,
        summary=summary,
        suggested_visual=suggest_visual(plan),
        suggested_followups=followups,
        generation_mode="fallback",
        query_result=result,
    )


def _extract_response_text(payload: dict[str, Any]) -> str:
    output = payload.get("output", [])
    chunks: list[str] = []
    for item in output:
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                text = content.get("text")
                if text:
                    chunks.append(text)
    return "\n".join(chunks).strip()


# Structured Outputs (Responses API `text.format`) -- forca a OpenAI a devolver
# exatamente esse formato, eliminando a classe de erro corrigida em
# 2026-07-01 (`y_axis` vindo como string em vez de lista). Modo strict exige
# todo campo em `required`; campos opcionais usam `type: [T, "null"]`.
_ANSWER_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "answer_markdown": {"type": "string"},
        "summary": {"type": "string"},
        "suggested_visual": {
            "type": "object",
            "properties": {
                "type": {"type": "string"},
                "x_axis": {"type": ["string", "null"]},
                "y_axis": {"type": "array", "items": {"type": "string"}},
                "title": {"type": ["string", "null"]},
            },
            "required": ["type", "x_axis", "y_axis", "title"],
            "additionalProperties": False,
        },
        "suggested_followups": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["answer_markdown", "summary", "suggested_visual", "suggested_followups"],
    "additionalProperties": False,
}


def generate_openai_answer(plan: PlannedQuery, result: RoyaltyQueryResult) -> RoyaltyAnswer:
    settings = load_app_settings()
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY nao configurada.")

    system_prompt = load_system_prompt()
    rows_preview = _prepare_llm_rows(plan, result)
    user_prompt = {
        "question": plan.question,
        "plan": plan.model_dump(),
        "rows_preview": rows_preview,
        "row_count": result.row_count,
        "metric_totals": _metric_totals(plan, result),
        "suggested_visual": suggest_visual(plan),
    }
    response = requests.post(
        "https://api.openai.com/v1/responses",
        headers={
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.openai_model,
            "instructions": system_prompt,
            "input": json.dumps(user_prompt, ensure_ascii=False),
            "temperature": 0.2,
            "max_output_tokens": 800,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "royalty_answer",
                    "schema": _ANSWER_JSON_SCHEMA,
                    "strict": True,
                }
            },
        },
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    text = _extract_response_text(payload)
    data = json.loads(text)

    return RoyaltyAnswer(
        answer_markdown=data["answer_markdown"],
        summary=data["summary"],
        suggested_visual=data.get("suggested_visual"),
        suggested_followups=data.get("suggested_followups", []),
        generation_mode="openai",
        query_result=result,
    )


def ask_royalties(request: RoyaltyQueryRequest) -> tuple[PlannedQuery, RoyaltyAnswer]:
    plan, result = run_royalty_query(request)
    try:
        answer = generate_openai_answer(plan, result)
    except Exception:
        answer = build_fallback_answer(plan, result)
    return plan, answer
