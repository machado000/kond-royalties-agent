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


def test_build_query_gravadora_dimension_resolves_subquery() -> None:
    plan = PlannedQuery(
        question="teste",
        source="royalty_performance",
        metrics=["revenue"],
        dimensions=["gravadora"],
    )

    sql = build_royalty_query_sql(plan)

    assert "dim_artistas" in sql
    assert "matched_artista_id" in sql
    assert "as gravadora" in sql


def test_build_query_dsu_artist_uses_raw_name() -> None:
    plan = PlannedQuery(
        question="teste",
        source="dsu_detail",
        metrics=["revenue"],
        dimensions=["artist"],
    )

    sql = build_royalty_query_sql(plan)

    assert "artista as artist" in sql
    assert "from public.vw_dsu_contratos_calendario" in sql


def test_build_query_dsu_dia_critico_dimension() -> None:
    plan = PlannedQuery(
        question="teste",
        source="dsu_detail",
        metrics=["shows"],
        dimensions=["dia_critico"],
    )

    sql = build_royalty_query_sql(plan)

    assert "dia_critico as dia_critico" in sql


def test_build_query_warner_chappell_platform_joins_exploitation_source() -> None:
    plan = PlannedQuery(
        question="teste",
        source="warner_chappell_detail",
        metrics=["revenue"],
        dimensions=["platform"],
    )

    sql = build_royalty_query_sql(plan)

    assert "dim_exploitation_source" in sql
    assert "descricao_canal" in sql


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
