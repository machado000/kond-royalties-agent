"""Carregamento de configuracoes locais do agente."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


ROOT_DIR = Path(__file__).resolve().parent.parent


class BigQuerySourceConfig(BaseModel):
    project_id: str
    datasets: list[str] = Field(default_factory=list)
    logical_sources: dict[str, dict[str, object]] = Field(default_factory=dict)


class AppSettings(BaseModel):
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    google_application_credentials: str | None = None
    bigquery_project_id: str | None = None
    bigquery_datasets: list[str] = Field(default_factory=list)


def _read_yaml(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Arquivo YAML invalido: {path}")
    return data


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def load_app_settings() -> AppSettings:
    _load_dotenv(ROOT_DIR / ".env")
    raw_datasets = os.getenv("BIGQUERY_DATASETS", "")
    datasets = [item.strip() for item in raw_datasets.split(",") if item.strip()]

    return AppSettings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        google_application_credentials=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
        bigquery_project_id=os.getenv("BIGQUERY_PROJECT_ID"),
        bigquery_datasets=datasets,
    )


def load_bigquery_source_config() -> BigQuerySourceConfig:
    data = _read_yaml(ROOT_DIR / "config" / "bigquery_sources.yml")
    return BigQuerySourceConfig.model_validate(data)
