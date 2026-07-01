from mcp_server.models import PlannedQuery, RoyaltyQueryResult
from mcp_server.responder import build_fallback_answer, suggest_visual


def test_suggest_visual_for_artist() -> None:
    plan = PlannedQuery(question="teste", metrics=["revenue"], dimensions=["artist"])
    assert suggest_visual(plan) == "barras por artista"


def test_build_fallback_answer_uses_top_row() -> None:
    plan = PlannedQuery(question="teste", metrics=["revenue", "royalties"], dimensions=["artist"])
    result = RoyaltyQueryResult(
        sql="select 1",
        rows=[
            {"artist": "Artista A", "revenue": 1000.0, "royalties": 100.0},
            {"artist": "Artista B", "revenue": 100.0, "royalties": 10.0},
        ],
        row_count=2,
        source_tables=["marts.royalty_performance"],
    )

    answer = build_fallback_answer(plan, result)

    assert "Artista A" in answer.answer_markdown
    assert "lidera em revenue" in answer.summary
