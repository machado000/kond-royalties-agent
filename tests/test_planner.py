from datetime import date

from mcp_server.models import RoyaltyQueryRequest
from mcp_server.planner import plan_royalty_query


def test_plan_infers_metrics_dimensions_and_date_range() -> None:
    request = RoyaltyQueryRequest(
        question="Como foram quantidade e receita por artista nos ultimos 7 dias?"
    )

    plan = plan_royalty_query(request, today=date(2026, 6, 26))

    assert plan.metrics == ["quantity", "revenue"]
    assert "artist" in plan.dimensions
    assert plan.date_range is not None
    assert plan.date_range.start_date == "2026-06-20"
    assert plan.date_range.end_date == "2026-06-26"


def test_plan_infers_origem_filter() -> None:
    request = RoyaltyQueryRequest(question="Mostre receita da Orchard por tipo de receita")

    plan = plan_royalty_query(request, today=date(2026, 6, 26))

    assert plan.filters["origem"] == "Orchard"
    assert "revenue_type" in plan.dimensions
