"""Catalogo semantico do agente."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from mcp_server.settings import ROOT_DIR


class CatalogItem(BaseModel):
    label: str | None = None
    description: str | None = None
    expression_hint: str | None = None


class SourceCatalog(BaseModel):
    default: bool = False
    description: str | None = None
    metrics: dict[str, CatalogItem] = Field(default_factory=dict)
    dimensions: dict[str, CatalogItem] = Field(default_factory=dict)


class SemanticCatalog(BaseModel):
    sources: dict[str, SourceCatalog] = Field(default_factory=dict)
    approved_sources: list[str] = Field(default_factory=list)

    @property
    def default_source(self) -> str:
        for name, source in self.sources.items():
            if source.default:
                return name
        return next(iter(self.sources), "royalty_performance")


def load_semantic_catalog(path: Path | None = None) -> SemanticCatalog:
    catalog_path = path or ROOT_DIR / "semantic_catalog" / "catalog.yml"
    with catalog_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    return SemanticCatalog.model_validate(data)


def build_catalog_payload() -> dict[str, object]:
    catalog = load_semantic_catalog()
    return {
        "version": "v2",
        "default_source": catalog.default_source,
        "sources": {
            name: {
                "description": source.description,
                "metrics": {n: item.model_dump() for n, item in source.metrics.items()},
                "dimensions": {n: item.model_dump() for n, item in source.dimensions.items()},
            }
            for name, source in catalog.sources.items()
        },
        "approved_sources": catalog.approved_sources,
    }
