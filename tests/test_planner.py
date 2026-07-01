from datetime import date

from mcp_server.models import MarketingQueryRequest
from mcp_server.planner import plan_marketing_query


def test_plan_infers_metrics_dimensions_and_date_range() -> None:
    request = MarketingQueryRequest(
        question="Como foi receita, investimento e ROAS por canal nos ultimos 7 dias?"
    )

    plan = plan_marketing_query(request, today=date(2026, 6, 26))

    assert plan.metrics == ["revenue", "spend", "roas"]
    assert "channel" in plan.dimensions
    assert plan.date_range is not None
    assert plan.date_range.start_date == "2026-06-20"
    assert plan.date_range.end_date == "2026-06-26"


def test_plan_infers_platform_filter() -> None:
    request = MarketingQueryRequest(question="Mostre conversões do Google Ads por campanha")

    plan = plan_marketing_query(request, today=date(2026, 6, 26))

    assert plan.filters["platform"] == "google_ads"
    assert "campaign" in plan.dimensions
