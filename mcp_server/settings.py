"""Carregamento de configuracoes locais do agente."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


ROOT_DIR = Path(__file__).resolve().parent.parent


class PostgresSourceConfig(BaseModel):
    schemas: list[str] = Field(default_factory=list)
    query_schema: str
    query_table: str
    logical_sources: dict[str, dict[str, object]] = Field(default_factory=dict)

    @property
    def qualified_table(self) -> str:
        return f"{self.query_schema}.{self.query_table}"


class AppSettings(BaseModel):
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    database_url: str | None = None
    pg_host: str | None = None
    pg_port: str | None = None
    pg_database: str | None = None
    pg_user: str | None = None
    pg_password: str | None = None
    pg_sslmode: str | None = None
    postgres_schemas: list[str] = Field(default_factory=list)


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
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(key.strip(), value)


def load_app_settings() -> AppSettings:
    _load_dotenv(ROOT_DIR / ".env")
    raw_schemas = os.getenv("POSTGRES_SCHEMAS", "")
    schemas = [item.strip() for item in raw_schemas.split(",") if item.strip()]

    return AppSettings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        database_url=os.getenv("DATABASE_URL") or None,
        pg_host=os.getenv("PGHOST"),
        pg_port=os.getenv("PGPORT"),
        pg_database=os.getenv("PGDATABASE"),
        pg_user=os.getenv("PGUSER"),
        pg_password=os.getenv("PGPASSWORD"),
        pg_sslmode=os.getenv("PGSSLMODE"),
        postgres_schemas=schemas,
    )


def load_postgres_source_config() -> PostgresSourceConfig:
    data = _read_yaml(ROOT_DIR / "config" / "postgres_sources.yml")
    connection = data.get("connection", {}) or {}
    query_source = data.get("query_source", {}) or {}
    return PostgresSourceConfig(
        schemas=connection.get("schemas", []),
        query_schema=query_source["schema"],
        query_table=query_source["table"],
        logical_sources=data.get("logical_sources", {}),
    )
