"""Planejamento semantico inicial para perguntas de performance de royalties."""

from __future__ import annotations

import re
import unicodedata
from datetime import date, timedelta

from mcp_server.models import DateRange, PlannedQuery, RoyaltyQueryRequest


DEFAULT_METRICS = ["quantity", "revenue"]
DEFAULT_DIMENSION = ["artist"]

METRIC_KEYWORDS = {
    "quantity": ["quantidade", "streams", "unidades", "shows", "quantity"],
    "revenue": ["receita", "royalties", "repasse", "faturamento", "revenue"],
}

DIMENSION_KEYWORDS = {
    "artist": ["artista", "artist"],
    "origem": ["origem", "distribuidora", "sistema de origem"],
    "revenue_type": ["tipo de receita", "categoria de receita", "revenue type"],
    "period": ["periodo", "por mes", "por data", "mensal"],
}

# Valores gravados na coluna `origem` (ver config/column_dictionary.yml).
# 'Warner Chappel' e a grafia real no banco (uma letra 'l'), diferente do
# nome do schema Postgres `warner_chappell` (duas letras 'l').
FILTER_KEYWORDS = {
    "origem": {
        "DSU": ["dsu"],
        "Omie": ["omie"],
        "Orchard": ["orchard"],
        "Universal": ["universal"],
        "Warner Chappel": ["warner chappell", "warner chappel"],
        "Warner Music": ["warner music"],
    },
    "revenue_type": {
        "Editora": ["editora", "publishing"],
        "Gravadora": ["gravadora", "master"],
        "Publicidade": ["publicidade", "advertising"],
        "Shows": ["shows", "show ao vivo"],
    },
}


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def infer_metrics(question: str) -> list[str]:
    normalized = _normalize(question)
    metrics = [name for name, keywords in METRIC_KEYWORDS.items() if any(word in normalized for word in keywords)]
    return metrics or DEFAULT_METRICS.copy()


def infer_dimensions(question: str) -> list[str]:
    normalized = _normalize(question)
    dimensions = [
        name for name, keywords in DIMENSION_KEYWORDS.items() if any(word in normalized for word in keywords)
    ]
    return dimensions or DEFAULT_DIMENSION.copy()


def infer_filters(question: str) -> dict[str, str]:
    normalized = _normalize(question)

    filters: dict[str, str] = {}
    for field, mapping in FILTER_KEYWORDS.items():
        for value, keywords in mapping.items():
            if any(_normalize(keyword) in normalized for keyword in keywords):
                filters[field] = value
                break
    return filters


def infer_date_range(question: str, today: date | None = None) -> DateRange | None:
    normalized = _normalize(question)
    reference = today or date.today()

    explicit_dates = re.findall(r"\b\d{4}-\d{2}-\d{2}\b", question)
    if len(explicit_dates) >= 2:
        return DateRange(start_date=explicit_dates[0], end_date=explicit_dates[1])
    if len(explicit_dates) == 1:
        return DateRange(start_date=explicit_dates[0], end_date=explicit_dates[0])

    day_match = re.search(r"(ultimos|ultimas|last)\s+(\d+)\s+dias", normalized)
    if day_match:
        days = int(day_match.group(2))
        start = reference - timedelta(days=max(days - 1, 0))
        return DateRange(start_date=start.isoformat(), end_date=reference.isoformat())

    if "ontem" in normalized or "yesterday" in normalized:
        target = reference - timedelta(days=1)
        return DateRange(start_date=target.isoformat(), end_date=target.isoformat())

    if "hoje" in normalized or "today" in normalized:
        return DateRange(start_date=reference.isoformat(), end_date=reference.isoformat())

    if "ultima semana" in normalized or "last week" in normalized:
        start = reference - timedelta(days=6)
        return DateRange(start_date=start.isoformat(), end_date=reference.isoformat())

    if "ultimo mes" in normalized or "last month" in normalized:
        start = reference - timedelta(days=29)
        return DateRange(start_date=start.isoformat(), end_date=reference.isoformat())

    return None


def plan_royalty_query(request: RoyaltyQueryRequest, today: date | None = None) -> PlannedQuery:
    metrics = request.metrics or infer_metrics(request.question)
    dimensions = request.dimensions or infer_dimensions(request.question)
    date_range = request.date_range or infer_date_range(request.question, today=today)
    filters = {**infer_filters(request.question), **request.filters}

    notes: list[str] = []
    if not request.metrics:
        notes.append("Metricas inferidas a partir da pergunta.")
    if not request.dimensions:
        notes.append("Dimensoes inferidas a partir da pergunta.")
    if date_range is None:
        notes.append("Sem intervalo explicito; a consulta usara todo o historico disponivel.")
    if date_range is not None:
        notes.append("Dados armazenados em grao mensal (period); o intervalo de datas e truncado para o mes.")

    return PlannedQuery(
        question=request.question,
        metrics=metrics,
        dimensions=dimensions,
        date_range=date_range,
        filters=filters,
        limit=request.limit,
        notes=notes,
    )
