from mcp_server.settings import load_bigquery_source_config


def test_bigquery_sources_config_loads() -> None:
    config = load_bigquery_source_config()

    assert config.project_id == "mistral-analytics"
    assert "google_ads" in config.datasets
