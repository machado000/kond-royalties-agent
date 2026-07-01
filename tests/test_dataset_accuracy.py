"""Validacao de acuracia entre os 3 datasets GA4.

ga4_bronze, ga4_silver e analytics_253977277 contem os mesmos dados em
granularidades diferentes. Este teste confirma que os 3 retornam receita
identica por canal para um periodo comum.

Requer acesso ao BigQuery (mistral-analytics). Marcado como 'slow' para
nao rodar no CI padrao — execute com: pytest -m slow
"""

from __future__ import annotations

import pytest

from mcp_server.models import MarketingQueryRequest
from mcp_server.planner import plan_marketing_query
from mcp_server.query_builder import build_marketing_query_sql
from mcp_server.query_runner import run_planned_query


def _revenue_by_channel(dataset: str, start: str, end: str) -> dict[str, float]:
    question = f"Receita por canal de {start} a {end} no {dataset}"
    request = MarketingQueryRequest(question=question, limit=100)
    plan = plan_marketing_query(request)
    result = run_planned_query(plan)
    return {
        row["channel"]: round(row["revenue"], 2)
        for row in result.rows
        if row["revenue"] > 0
    }


@pytest.mark.slow
def test_revenue_matches_across_datasets() -> None:
    start, end = "2026-06-19", "2026-06-23"

    bronze = _revenue_by_channel("ga4_bronze", start, end)
    silver = _revenue_by_channel("ga4_silver", start, end)
    raw = _revenue_by_channel("analytics_253977277", start, end)

    assert bronze, "ga4_bronze retornou zero receita"
    assert silver, "ga4_silver retornou zero receita"
    assert raw, "analytics_253977277 retornou zero receita"

    assert bronze == raw, (
        f"bronze != raw\n"
        f"  bronze: {bronze}\n"
        f"  raw:    {raw}"
    )
    assert silver == raw, (
        f"silver != raw\n"
        f"  silver: {silver}\n"
        f"  raw:    {raw}"
    )

    bronze_total = sum(bronze.values())
    silver_total = sum(silver.values())
    raw_total = sum(raw.values())
    assert bronze_total == silver_total == raw_total


@pytest.mark.slow
def test_total_revenue_is_positive() -> None:
    start, end = "2026-06-19", "2026-06-23"
    raw = _revenue_by_channel("analytics_253977277", start, end)
    assert sum(raw.values()) > 0, "Receita total deve ser positiva"
