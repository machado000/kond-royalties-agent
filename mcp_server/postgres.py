"""Utilitarios de Postgres para o servidor MCP."""

from __future__ import annotations

from mcp_server.settings import AppSettings


SYSTEM_SCHEMAS = {"pg_catalog", "information_schema", "pg_toast"}


def _is_system_schema(schema_name: str) -> bool:
    return schema_name in SYSTEM_SCHEMAS or schema_name.startswith("pg_temp_") or schema_name.startswith(
        "pg_toast_temp_"
    )


def _build_conninfo(settings: AppSettings) -> str:
    if settings.database_url:
        return settings.database_url

    if not settings.pg_host:
        raise ValueError(
            "Configure DATABASE_URL ou PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD/PGSSLMODE no .env."
        )

    from psycopg.conninfo import make_conninfo

    params = {
        "host": settings.pg_host,
        "port": settings.pg_port,
        "dbname": settings.pg_database,
        "user": settings.pg_user,
        "password": settings.pg_password,
        "sslmode": settings.pg_sslmode,
    }
    return make_conninfo(**{key: value for key, value in params.items() if value})


def create_connection(settings: AppSettings):
    try:
        import psycopg
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "Dependencia ausente: instale psycopg[binary] antes de conectar ao Postgres."
        ) from exc

    connection = psycopg.connect(_build_conninfo(settings))
    if settings.postgres_schemas:
        schema_list = ", ".join(settings.postgres_schemas)
        with connection.cursor() as cursor:
            cursor.execute(f"SET search_path TO {schema_list}")
        connection.commit()
    return connection


def list_accessible_schemas(settings: AppSettings) -> list[str]:
    connection = create_connection(settings)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                select schema_name
                from information_schema.schemata
                order by schema_name
                """
            )
            all_schemas = [row[0] for row in cursor.fetchall()]
    finally:
        connection.close()
    return [schema for schema in all_schemas if not _is_system_schema(schema)]


def describe_schema(
    settings: AppSettings, schema: str | None = None
) -> dict[str, dict[str, list[dict[str, str]]]]:
    """Introspecta tabelas e colunas via information_schema.

    Retorna ``{schema: {table: [{"column", "data_type", "is_nullable"}, ...]}}``.
    Substitui, para Postgres, a antiga listagem de datasets/tabelas do BigQuery
    — permite descobrir o schema real do banco em vez de depender de um
    dicionario de colunas mantido a mao.
    """
    target_schemas = [schema] if schema else settings.postgres_schemas
    if not target_schemas:
        target_schemas = list_accessible_schemas(settings)

    connection = create_connection(settings)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                select table_schema, table_name, column_name, data_type, is_nullable
                from information_schema.columns
                where table_schema = any(%s)
                order by table_schema, table_name, ordinal_position
                """,
                (target_schemas,),
            )
            rows = cursor.fetchall()
    finally:
        connection.close()

    result: dict[str, dict[str, list[dict[str, str]]]] = {}
    for table_schema, table_name, column_name, data_type, is_nullable in rows:
        tables = result.setdefault(table_schema, {})
        columns = tables.setdefault(table_name, [])
        columns.append(
            {
                "column": column_name,
                "data_type": data_type,
                "is_nullable": is_nullable,
            }
        )
    return result
