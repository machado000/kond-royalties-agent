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

    assert "revenue" in default_source["metrics"]
    assert "artist" in default_source["dimensions"]


def test_detail_source_has_track_dimension() -> None:
    payload = build_catalog_payload()

    assert "track" in payload["sources"]["orchard_detail"]["dimensions"]
    assert "track" not in payload["sources"]["royalty_performance"]["dimensions"]
