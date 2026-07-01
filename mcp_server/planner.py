"""Planejamento semantico inicial para perguntas de marketing."""

from __future__ import annotations

import re
import unicodedata
from datetime import date, timedelta

from mcp_server.models import DateRange, MarketingQueryRequest, PlannedQuery


DEFAULT_METRICS = ["revenue", "spend", "roas"]
DEFAULT_DIMENSION = ["channel"]

METRIC_KEYWORDS = {
    "revenue": ["receita", "faturamento", "revenue", "gmv", "vendas"],
    "spend": ["investimento", "gasto", "spend", "custo", "midia"],
    "roas": ["roas", "retorno"],
    "conversions": ["conversoes", "conversão", "conversion", "conversions", "pedidos", "orders"],
    "sessions": ["sessoes", "sessões", "sessions", "trafego", "tráfego"],
}

DIMENSION_KEYWORDS = {
    "channel": ["canal", "channel", "origem"],
    "platform": ["plataforma", "platform", "fonte", "midia"],
    "campaign": ["campanha", "campaign"],
    "date": ["por dia", "por data", "date", "diario", "diaria", "daily"],
}

KNOWN_DATASETS = [
    "analytics_253977277",
    "ga4_bronze",
    "ga4_silver",
    "google_ads",
    "facebook_ads_bronze",
    "facebook_ads_silver",
]

FILTER_KEYWORDS = {
    "platform": {
        "google_ads": ["google ads", "google", "adwords"],
        "facebook_ads": ["facebook ads", "meta ads", "facebook", "meta", "instagram"],
        "ga4": ["ga4", "analytics", "google analytics"],
    },
    "channel": {
        "paid_search": ["paid search", "busca paga", "pesquisa paga"],
        "paid_social": ["paid social", "social pago", "social paga"],
        "organic_search": ["organic", "organico", "orgânico"],
        "email": ["email", "newsletter"],
        "direct": ["direct", "direto"],
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


def _mask_dataset_names(text: str, datasets: list[str]) -> str:
    masked = text
    for ds in datasets:
        masked = masked.replace(ds, " ")
        masked = masked.replace(ds.replace("_", " "), " ")
    return masked


def infer_filters(question: str) -> dict[str, str]:
    normalized = _normalize(question)
    detected_datasets = infer_source_datasets(question)
    masked = _mask_dataset_names(normalized, detected_datasets)

    filters: dict[str, str] = {}
    for field, mapping in FILTER_KEYWORDS.items():
        for value, keywords in mapping.items():
            if any(keyword in masked for keyword in keywords):
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

    if "ultimo mes" in normalized or "último mês" in question.lower() or "last month" in normalized:
        start = reference - timedelta(days=29)
        return DateRange(start_date=start.isoformat(), end_date=reference.isoformat())

    return None


def infer_source_datasets(question: str) -> list[str]:
    normalized = _normalize(question)
    return [ds for ds in KNOWN_DATASETS if ds in normalized]


def plan_marketing_query(request: MarketingQueryRequest, today: date | None = None) -> PlannedQuery:
    metrics = request.metrics or infer_metrics(request.question)
    dimensions = request.dimensions or infer_dimensions(request.question)
    date_range = request.date_range or infer_date_range(request.question, today=today)
    filters = {**infer_filters(request.question), **request.filters}
    source_datasets = infer_source_datasets(request.question)

    notes: list[str] = []
    if not request.metrics:
        notes.append("Metricas inferidas a partir da pergunta.")
    if not request.dimensions:
        notes.append("Dimensoes inferidas a partir da pergunta.")
    if date_range is None:
        notes.append("Sem intervalo explicito; a consulta usara todo o historico disponivel.")
    if source_datasets:
        notes.append(f"Datasets explícitos: {', '.join(source_datasets)}.")
    else:
        notes.append("Usando camada semântica padrão (todas as fontes).")

    return PlannedQuery(
        question=request.question,
        metrics=metrics,
        dimensions=dimensions,
        date_range=date_range,
        filters=filters,
        source_datasets=source_datasets,
        limit=request.limit,
        notes=notes,
    )
