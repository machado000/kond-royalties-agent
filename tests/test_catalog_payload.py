from mcp_server.catalog import build_catalog_payload


def test_catalog_payload_has_expected_keys() -> None:
    payload = build_catalog_payload()

    assert payload["version"] == "v2"
    assert payload["default_source"] == "royalty_performance"
    assert "sources" in payload
    assert "royalty_performance" in payload["sources"]
    assert "orchard_detail" in payload["sources"]
    assert "approved_sources" in payload


def test_default_source_has_metrics_and_dimensions() -> None:
    payload = build_catalog_payload()
    default_source = payload["sources"][payload["default_source"]]

    assert "royalties" in default_source["metrics"]
    assert "artist" in default_source["dimensions"]


def test_omie_detail_has_receita_custo_metrics() -> None:
    payload = build_catalog_payload()
    omie_metrics = payload["sources"]["omie_detail"]["metrics"]

    assert "revenue" in omie_metrics
    assert "cost" in omie_metrics


def test_royalty_sources_never_expose_revenue_or_cost_keys() -> None:
    # Garante a separacao de dominio (ver nota no topo de
    # semantic_catalog/catalog.yml): fontes de royalty usam a chave
    # "royalties", nunca "revenue"/"cost" (exclusivas de omie_detail).
    payload = build_catalog_payload()
    royalty_sources = [
        "royalty_performance",
        "dsu_detail",
        "orchard_detail",
        "somlivre_detail",
        "universal_detail",
        "warner_chappell_detail",
        "warner_music_detail",
    ]
    for name in royalty_sources:
        metrics = payload["sources"][name]["metrics"]
        assert "royalties" in metrics
        assert "revenue" not in metrics
        assert "cost" not in metrics


def test_omie_detail_does_not_expose_royalties_key() -> None:
    payload = build_catalog_payload()

    assert "royalties" not in payload["sources"]["omie_detail"]["metrics"]


def test_detail_source_has_track_dimension() -> None:
    payload = build_catalog_payload()

    assert "track" in payload["sources"]["orchard_detail"]["dimensions"]
    assert "track" not in payload["sources"]["royalty_performance"]["dimensions"]


def test_royalty_performance_has_gravadora_dimension() -> None:
    payload = build_catalog_payload()

    assert "gravadora" in payload["sources"]["royalty_performance"]["dimensions"]


def test_warner_chappell_detail_has_platform_dimension() -> None:
    payload = build_catalog_payload()

    assert "platform" in payload["sources"]["warner_chappell_detail"]["dimensions"]
