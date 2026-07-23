"""Analises de qualidade de agendamento DSU (dia_critico).

Consultas bespoke sobre `public.vw_dsu_contratos_calendario` (dedup por
contrato + join com `dim_calendario`, ver `config/column_dictionary.yml`)
que nao se encaixam no modelo metrica+dimensao de `query_builder.py` (a
segunda precisa de anti-join para achar datas sem contrato). Espelha as
duas queries de `.claude/skills/dsu-dia-critico/SKILL.md` -- manter as
duas em sincronia se uma mudar.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from mcp_server.models import RoyaltyQueryResult
from mcp_server.postgres import create_connection
from mcp_server.settings import load_app_settings


_SOURCE_TABLES = ["public.vw_dsu_contratos_calendario", "public.dim_calendario"]


def _normalize_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def _run_sql(sql: str, params: dict[str, Any]) -> RoyaltyQueryResult:
    connection = create_connection(load_app_settings())
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            columns = [column.name for column in cursor.description]
            rows = [
                {column: _normalize_value(value) for column, value in zip(columns, row)}
                for row in cursor.fetchall()
            ]
    finally:
        connection.close()
    return RoyaltyQueryResult(sql=sql, rows=rows, row_count=len(rows), source_tables=_SOURCE_TABLES)


_BOOKING_QUALITY_SQL = """
select
  artista,
  count(*) as total_shows,
  count(*) filter (where dia_critico) as shows_dia_critico,
  round(100.0 * count(*) filter (where dia_critico) / nullif(count(*), 0), 1) as pct_dia_critico
from vw_dsu_contratos_calendario
where status = 'CONFIRMADO'
  and dia_critico is not null
  and (%(artist)s::text is null or artista = %(artist)s)
group by artista
order by pct_dia_critico desc
""".strip()


def get_dsu_booking_quality(artist: str | None = None) -> RoyaltyQueryResult:
    """% dos shows CONFIRMADO de cada artista (ou de um artista especifico) em dia_critico.

    So considera `status = 'CONFIRMADO'` e contratos com `dt_show` a
    partir de 2026-01-01 (cobertura de `dim_calendario`).
    """
    return _run_sql(_BOOKING_QUALITY_SQL, {"artist": artist})


_MISSED_OPPORTUNITIES_SQL = """
with booked as (
  select artista, dt_show
  from vw_dsu_contratos_calendario
  where status = 'CONFIRMADO'
),
artists as (
  select distinct artista from vw_dsu_contratos_calendario
),
future_critical_days as (
  select data from dim_calendario
  where dia_critico and data between current_date and current_date + %(lookahead_days)s
)
select a.artista, f.data as data_livre
from artists a
cross join future_critical_days f
left join booked b on b.artista = a.artista and b.dt_show = f.data
where b.dt_show is null
  and (%(artist)s::text is null or a.artista = %(artist)s)
order by a.artista, f.data
""".strip()


def get_dsu_missed_opportunities(artist: str | None = None, lookahead_days: int = 90) -> RoyaltyQueryResult:
    """Datas futuras de dia_critico sem contrato CONFIRMADO, por artista.

    Uma data com so um contrato `FINANCEIRO/AGUARDAR` (nao confirmado)
    ainda aparece aqui como livre -- decisao deliberada, so conta o que e
    certo. Um artista com a agenda 100% ocupada na janela simplesmente
    nao aparece no resultado.
    """
    return _run_sql(_MISSED_OPPORTUNITIES_SQL, {"artist": artist, "lookahead_days": lookahead_days})
