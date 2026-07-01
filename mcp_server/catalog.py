"""Catalogo semantico do agente."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from mcp_server.settings import ROOT_DIR


class CatalogItem(BaseModel):
    label: str
    description: str | None = None
    expression_hint: str | None = None


class SemanticCatalog(BaseModel):
    metrics: dict[str, CatalogItem] = Field(default_factory=dict)
    dimensions: dict[str, CatalogItem] = Field(default_factory=dict)
    approved_sources: list[str] = Field(default_factory=list)


def load_semantic_catalog(path: Path | None = None) -> SemanticCatalog:
    catalog_path = path or ROOT_DIR / "semantic_catalog" / "catalog.yml"
    with catalog_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    return SemanticCatalog.model_validate(data)


def build_catalog_payload() -> dict[str, object]:
    catalog = load_semantic_catalog()
    return {
        "version": "v1",
        "metrics": {name: item.model_dump() for name, item in catalog.metrics.items()},
        "dimensions": {name: item.model_dump() for name, item in catalog.dimensions.items()},
        "approved_sources": catalog.approved_sources,
    }
