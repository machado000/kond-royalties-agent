from datetime import date

from mcp_server.models import RoyaltyQueryRequest
from mcp_server.planner import plan_royalty_query
from mcp_server.query_builder import build_royalty_query_sql


def test_build_query_uses_approved_dimensions_and_metrics() -> None:
    request = RoyaltyQueryRequest(
        question="Como foram quantidade e receita por artista nos ultimos 7 dias?"
    )
    plan = plan_royalty_query(request, today=date(2026, 6, 26))

    sql = build_royalty_query_sql(plan)

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
