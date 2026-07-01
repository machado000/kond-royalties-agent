from pathlib import Path


def test_sources_config_exists() -> None:
    assert Path("config/postgres_sources.yml").exists()
    assert Path("config/column_dictionary.yml").exists()
