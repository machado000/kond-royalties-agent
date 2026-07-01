"""Utilitarios de BigQuery para o servidor MCP."""

from __future__ import annotations

from mcp_server.settings import AppSettings


def create_bigquery_client(settings: AppSettings):
    try:
        from google.cloud import bigquery
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "Dependencia ausente: instale google-cloud-bigquery antes de usar o diagnostico."
        ) from exc

    project_id = settings.bigquery_project_id
    if not project_id:
        raise ValueError("BIGQUERY_PROJECT_ID nao configurado.")
    return bigquery.Client(project=project_id)


def list_accessible_datasets(settings: AppSettings) -> list[str]:
    client = create_bigquery_client(settings)
    datasets = client.list_datasets()
    return sorted(dataset.dataset_id for dataset in datasets)
