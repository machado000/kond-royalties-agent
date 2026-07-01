"""Execucao controlada de consultas de royalties."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from mcp_server.models import PlannedQuery, RoyaltyQueryRequest, RoyaltyQueryResult
from mcp_server.planner import plan_royalty_query
from mcp_server.postgres import create_connection
from mcp_server.query_builder import build_royalty_query_sql, get_source_tables
from mcp_server.settings import load_app_settings


def _normalize_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    return value


def run_planned_query(plan: PlannedQuery) -> RoyaltyQueryResult:
    sql = build_royalty_query_sql(plan)
    connection = create_connection(load_app_settings())
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            columns = [column.name for column in cursor.description]
            rows = [
                {column: _normalize_value(value) for column, value in zip(columns, row)}
                for row in cursor.fetchall()
            ]
    finally:
        connection.close()
    return RoyaltyQueryResult(
        sql=sql,
        rows=rows,
        row_count=len(rows),
        source_tables=get_source_tables(plan),
    )


def run_royalty_query(request: RoyaltyQueryRequest) -> tuple[PlannedQuery, RoyaltyQueryResult]:
    plan = plan_royalty_query(request)
    result = run_planned_query(plan)
    return plan, result
