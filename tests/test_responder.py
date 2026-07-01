from mcp_server.models import MarketingQueryResult, PlannedQuery
from mcp_server.responder import build_fallback_answer, suggest_visual


def test_suggest_visual_for_channel() -> None:
    plan = PlannedQuery(question="teste", metrics=["revenue"], dimensions=["channel"])
    assert suggest_visual(plan) == "barras por canal"


def test_build_fallback_answer_uses_top_row() -> None:
    plan = PlannedQuery(question="teste", metrics=["revenue", "spend"], dimensions=["channel"])
    result = MarketingQueryResult(
        sql="select 1",
        rows=[
            {"channel": "paid_search", "revenue": 1000.0, "spend": 100.0},
            {"channel": "email", "revenue": 100.0, "spend": 0.0},
        ],
        row_count=2,
        source_tables=["a"],
    )

    answer = build_fallback_answer(plan, result)

    assert "paid_search" in answer.answer_markdown
    assert "lidera em revenue" in answer.summary
