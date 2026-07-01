from pathlib import Path


def test_catalog_exists() -> None:
    assert Path("semantic_catalog/catalog.yml").exists()

