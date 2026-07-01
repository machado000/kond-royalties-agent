from mcp_server.catalog import build_catalog_payload


def test_catalog_payload_has_expected_keys() -> None:
    payload = build_catalog_payload()

    assert payload["version"] == "v1"
    assert "metrics" in payload
    assert "dimensions" in payload
    assert "approved_sources" in payload
