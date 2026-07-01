from datetime import date

from mcp_server.models import MarketingQueryRequest
from mcp_server.planner import plan_marketing_query
from mcp_server.query_builder import build_marketing_query_sql


def test_build_query_uses_approved_dimensions_and_metrics() -> None:
    request = MarketingQueryRequest(
        question="Como foi receita e ROAS por canal nos ultimos 7 dias?"
    )
    plan = plan_marketing_query(request, today=date(2026, 6, 26))

    sql = build_marketing_query_sql(plan)

    assert "sum(revenue) as revenue" in sql
    assert "sum(revenue) / nullif(sum(spend), 0) as roas" in sql
    assert "from base" in sql
    assert "group by 1" in sql
    assert "`mistral-analytics.google_ads.p_ads_ad_group_ad_8784814486`" in sql
