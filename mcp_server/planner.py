"""Planejamento semantico inicial para perguntas de performance de royalties."""

from __future__ import annotations

import re
import unicodedata
from datetime import date, timedelta

from mcp_server.catalog import load_semantic_catalog
from mcp_server.models import DateRange, PlannedQuery, RoyaltyQueryRequest


DEFAULT_SOURCE = "royalty_performance"
DEFAULT_METRICS = ["quantity", "royalties"]
DEFAULT_DIMENSION = ["artist"]

# Vocabulario de metrica deliberadamente separado por dominio (ver nota de
# separacao em semantic_catalog/catalog.yml): "royalties" so aparece em
# fontes de royalty, "revenue"/"cost" so em omie_detail (financeiro). Nunca
# unificar essas duas listas — e a garantia de que uma pergunta sobre
# "receita" nao acabe respondida com dados de royalty, e vice-versa.
METRIC_KEYWORDS = {
    "quantity": ["quantidade", "streams", "unidades", "shows", "quantity",
                 "reproduções", "reproducoes", "playback", "plays", "play"],
    "royalties": ["royalties", "royalty", "direitos autorais", "remuneracao autoral",
                  "remuneração autoral", "repasse", "arrecadação", "monetização"],
    "revenue": ["receita", "faturamento"],
    "cost": ["custo", "custos", "despesa", "despesas"],
}

DIMENSION_KEYWORDS = {
    "artist": ["artista", "artist", "cantor", "cantora", "banda", "grupo", "mc",
               "dj", "intérprete", "talento", "dupla", "projeto", "collab", "colab"],
    "origem": ["origem", "distribuidora", "sistema de origem", "publisher", "plataforma", "fonte"],
    "revenue_type": ["tipo de royalty", "categoria de royalty", "tipo de receita",
                     "categoria de receita", "revenue type", "tipo de arrecadacao",
                     "tipo de faturamento", "rubrica", "linha de receita"],
    "period": ["periodo", "por mes", "por data", "mensal", "anual", "trimestre", "semestre",
               "data", "dia", "ano", "mês", "temporalidade", "época", "período"],
    "track": ["faixa", "musica", "música", "cancao", "canção", "track", "som",
              "áudio", "single", "beat", "melodia", "composição", "obra", "fonograma"],
    "composer": ["compositor", "composer", "autor", "escritor", "letrista",
                 "coautor", "co-autor", "criador"],
    "isrc": ["isrc", "código isrc", "cod isrc", "registro isrc",
             "identificador", "id da faixa"],
    "territory": ["territorio", "pais", "country"],
    "platform": ["plataforma", "dsp", "canal", "loja", "serviço",
                 "app", "aplicativo", "streaming", "rede social"],
    "gravadora": ["gravadora", "label", "selo", "master", "master rights",
                  "produtora", "companhia", "produtora fonográfica"],
    "contratante": ["contratante", "cliente", "parceiro", "promotor",
                    "produtor de evento", "organizador", "patrocinador", "comprador"],
    "vendedor": ["vendedor", "responsavel comercial", "agente comercial", "comercial",
                 "executivo de contas", "representante", "booker", "negociador"],
    "tipo_evento": ["tipo de evento", "tipo evento", "formato do evento",
                    "categoria do evento", "estilo do evento", "formato de show"],
    "dia_critico": ["dia critico", "dia ideal", "noite livre", "dia de show", "dia de evento",
                    "data de evento", "dia principal", "data de show", "data chave"],
}

# Valores gravados na coluna `origem` (ver config/column_dictionary.yml).
# Omie NAO e um valor valido de `origem` aqui — foi removido de
# `royalty_performance` (ver semantic_catalog/catalog.yml); perguntas sobre
# Omie sao roteadas para a fonte `omie_detail` via SOURCE_STANDALONE_KEYWORDS.
FILTER_KEYWORDS = {
    "origem": {
        "DSU": ["dsu"],
        "Orchard": ["orchard"],
        "Universal": ["universal"],
        "Warner Chappell": ["warner chappell", "warner chappel", "warner chapel"],
        "Warner Music": ["warner music"],
    },
    "revenue_type": {
        "Editora": ["editora", "publisher", "publishing", "autoral", "direitos autorais"],
        "Gravadora": ["gravadora", "master", "label", "selo", "master rights"],
        "Publicidade": ["publicidade", "advertising"],
        "Shows": ["shows", "show ao vivo", "evento", "eventos", "contrato de show",
                  "apresentação", "apresentacoes", "bilheteria", "cachê", "cache",
                  "tour", "turnê", "turne", "gig", "conserto"],
    },
}

# Fontes que podem ser inferidas diretamente por palavra-chave, sem precisar
# de nivel de detalhe de faixa/musica (ver TRACK_LEVEL_KEYWORDS abaixo).
SOURCE_STANDALONE_KEYWORDS = {
    "dsu_detail": ["show", "shows", "evento", "eventos", "contrato de show"],
    "omie_detail": ["omie", "financeiro", "fluxo de caixa", "contas a pagar", "contas a receber",
                    "erp", "receita", "custo", "custos", "despesa", "despesas", "lucro", "resultado"],
}

# Fontes de detalhe por plataforma — so inferidas quando a pergunta tambem
# menciona algo em nivel de faixa/musica (a view unificada nao tem essa
# dimensao, entao mencionar so a plataforma nao basta para sair dela).
SOURCE_PLATFORM_KEYWORDS = {
    "orchard_detail": ["orchard"],
    "somlivre_detail": ["som livre", "somlivre", "sony music", "sony"],
    "universal_detail": ["universal"],
    "warner_chappell_detail": ["warner chappell", "warner chappel"],
    "warner_music_detail": ["warner music"],
}

TRACK_LEVEL_KEYWORDS = ["faixa", "musica", "compositor", "isrc", "obra", "cancao", "track"]


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def infer_source(question: str) -> str | None:
    normalized = _normalize(question)

    for source, keywords in SOURCE_STANDALONE_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return source

    if any(keyword in normalized for keyword in TRACK_LEVEL_KEYWORDS):
        for source, keywords in SOURCE_PLATFORM_KEYWORDS.items():
            if any(_normalize(keyword) in normalized for keyword in keywords):
                return source

    return None


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

    if "ultimo ano" in normalized or "last year" in normalized:
        start = reference - timedelta(days=364)
        return DateRange(start_date=start.isoformat(), end_date=reference.isoformat())

    return None


def plan_royalty_query(request: RoyaltyQueryRequest, today: date | None = None) -> PlannedQuery:
    catalog = load_semantic_catalog()

    source = request.source or infer_source(request.question) or DEFAULT_SOURCE
    if source not in catalog.sources:
        source = DEFAULT_SOURCE
    source_catalog = catalog.sources[source]

    metrics = request.metrics or infer_metrics(request.question)
    metrics = [m for m in metrics if m in source_catalog.metrics] or list(source_catalog.metrics)[:2]

    dimensions = request.dimensions or infer_dimensions(request.question)
    dimensions = [d for d in dimensions if d in source_catalog.dimensions] or list(source_catalog.dimensions)[:1]

    date_range = request.date_range or infer_date_range(request.question, today=today)
    filters = {**infer_filters(request.question), **request.filters}
    filters = {field: value for field, value in filters.items() if field in source_catalog.dimensions}

    notes: list[str] = []
    if not request.source:
        notes.append(f"Fonte inferida a partir da pergunta: '{source}'.")
    if not request.metrics:
        notes.append("Metricas inferidas a partir da pergunta.")
    if not request.dimensions:
        notes.append("Dimensoes inferidas a partir da pergunta.")
    if date_range is None:
        notes.append("Sem intervalo explicito; a consulta usara todo o historico disponivel.")
    if date_range is not None and "period" in source_catalog.dimensions:
        notes.append("Dados armazenados em grao mensal (period); o intervalo de datas e truncado para o mes.")
    if source != DEFAULT_SOURCE:
        notes.append(
            f"Fonte '{source}' e um detalhe de uma unica plataforma — nao combinar/agregar "
            "com a view unificada nem com outra fonte de detalhe."
        )

    return PlannedQuery(
        question=request.question,
        source=source,
        metrics=metrics,
        dimensions=dimensions,
        date_range=date_range,
        filters=filters,
        limit=request.limit,
        notes=notes,
    )
