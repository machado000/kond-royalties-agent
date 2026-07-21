from datetime import date

from mcp_server.models import RoyaltyQueryRequest
from mcp_server.planner import plan_royalty_query


def test_plan_infers_metrics_dimensions_and_date_range() -> None:
    request = RoyaltyQueryRequest(
        question="Como foram quantidade e receita por artista nos ultimos 7 dias?"
    )

    plan = plan_royalty_query(request, today=date(2026, 6, 26))

    assert plan.source == "royalty_performance"
    assert plan.metrics == ["quantity", "revenue"]
    assert "artist" in plan.dimensions
    assert plan.date_range is not None
    assert plan.date_range.start_date == "2026-06-20"
    assert plan.date_range.end_date == "2026-06-26"


def test_plan_infers_origem_filter() -> None:
    request = RoyaltyQueryRequest(question="Mostre receita da Orchard por tipo de receita")

    plan = plan_royalty_query(request, today=date(2026, 6, 26))

    assert plan.source == "royalty_performance"
    assert plan.filters["origem"] == "Orchard"
    assert "revenue_type" in plan.dimensions


def test_plan_infers_detail_source_from_track_level_question() -> None:
    request = RoyaltyQueryRequest(question="Quais faixas da Orchard mais tocaram por artista?")

    plan = plan_royalty_query(request, today=date(2026, 6, 26))

    assert plan.source == "orchard_detail"
    assert "track" in plan.dimensions
    assert "artist" in plan.dimensions


def test_plan_infers_dsu_source_from_show_keyword() -> None:
    request = RoyaltyQueryRequest(question="Quanto os shows geraram de receita por artista?")

    plan = plan_royalty_query(request, today=date(2026, 6, 26))

    assert plan.source == "dsu_detail"


def test_explicit_source_overrides_inference() -> None:
    request = RoyaltyQueryRequest(question="Receita por artista", source="universal_detail")

    plan = plan_royalty_query(request, today=date(2026, 6, 26))

    assert plan.source == "universal_detail"


def test_unknown_source_falls_back_to_default() -> None:
    request = RoyaltyQueryRequest(question="Receita por artista", source="does_not_exist")

    plan = plan_royalty_query(request, today=date(2026, 6, 26))

    assert plan.source == "royalty_performance"
