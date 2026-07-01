from pathlib import Path


def test_sources_config_exists() -> None:
    assert Path("config/bigquery_sources.yml").exists()
