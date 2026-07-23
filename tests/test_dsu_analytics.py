from datetime import date, datetime
from decimal import Decimal

from mcp_server.dsu_analytics import (
    _BOOKING_QUALITY_SQL,
    _MISSED_OPPORTUNITIES_SQL,
    _normalize_value,
)


def test_booking_quality_sql_filters_confirmado_only() -> None:
    assert "status = 'CONFIRMADO'" in _BOOKING_QUALITY_SQL
    assert "FINANCEIRO/AGUARDAR" not in _BOOKING_QUALITY_SQL
    assert "CANCELADO" not in _BOOKING_QUALITY_SQL


def test_booking_quality_sql_excludes_rows_without_calendar_coverage() -> None:
    assert "dia_critico is not null" in _BOOKING_QUALITY_SQL


def test_booking_quality_sql_queries_the_deduped_view() -> None:
    assert "from vw_dsu_contratos_calendario" in _BOOKING_QUALITY_SQL


def test_missed_opportunities_sql_uses_confirmado_and_anti_join() -> None:
    assert "status = 'CONFIRMADO'" in _MISSED_OPPORTUNITIES_SQL
    assert "left join booked" in _MISSED_OPPORTUNITIES_SQL
    assert "where b.dt_show is null" in _MISSED_OPPORTUNITIES_SQL


def test_normalize_value_converts_decimal_to_float() -> None:
    assert _normalize_value(Decimal("12.5")) == 12.5
    assert isinstance(_normalize_value(Decimal("12.5")), float)


def test_normalize_value_converts_date_to_isoformat_string() -> None:
    assert _normalize_value(date(2026, 8, 7)) == "2026-08-07"
    assert _normalize_value(datetime(2026, 8, 7, 10, 30)) == "2026-08-07T10:30:00"


def test_normalize_value_passes_through_other_types() -> None:
    assert _normalize_value("teste") == "teste"
    assert _normalize_value(None) is None
    assert _normalize_value(42) == 42
