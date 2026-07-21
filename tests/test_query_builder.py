from datetime import date

import pytest

from mcp_server.models import PlannedQuery, RoyaltyQueryRequest
from mcp_server.planner import plan_royalty_query
from mcp_server.query_builder import build_royalty_query_sql


def test_build_query_uses_approved_dimensions_and_metrics() -> None:
    request = RoyaltyQueryRequest(
        question="Como foram quantidade e receita por artista nos ultimos 7 dias?"
    )
    plan = plan_royalty_query(request, today=date(2026, 6, 26))

    sql = build_royalty_query_sql(plan)

    assert plan.source == "royalty_performance"
    assert "sum(quantity) as quantity" in sql
    assert "sum(revenue) as revenue" in sql
    assert "from public.vw_ft_dados_analiticos_union" in sql
    assert "group by 1" in sql
    assert "period >= '2026-06'" in sql
    assert "period <= '2026-06'" in sql


def test_build_query_applies_case_insensitive_filter() -> None:
    request = RoyaltyQueryRequest(question="Mostre receita da Orchard por tipo de receita")
    plan = plan_royalty_query(request, today=date(2026, 6, 26))

    sql = build_royalty_query_sql(plan)

    assert "lower(origem) = lower('Orchard')" in sql


def test_build_query_for_detail_source_resolves_expression_hints() -> None:
    request = RoyaltyQueryRequest(
        question="Quais faixas da Orchard mais tocaram por artista?",
        source="orchard_detail",
    )
    plan = plan_royalty_query(request, today=date(2026, 6, 26))

    sql = build_royalty_query_sql(plan)

    assert plan.source == "orchard_detail"
    assert "track" in plan.dimensions
    assert "from public.ft_orchard_dados_analiticos" in sql
    assert "titulo_musica as track" in sql


def test_build_query_rejects_metric_not_in_source() -> None:
    # PlannedQuery construido diretamente (nao via planner, que ja filtra
    # metricas invalidas) para exercitar a validacao do proprio query_builder.
    plan = PlannedQuery(
        question="teste",
        source="dsu_detail",
        metrics=["cost"],
        dimensions=["artist"],
    )

    with pytest.raises(ValueError, match="nao aprovadas"):
        build_royalty_query_sql(plan)
