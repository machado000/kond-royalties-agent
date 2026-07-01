"""Modelos base para o servidor MCP."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DateRange(BaseModel):
    start_date: str | None = None
    end_date: str | None = None


class MarketingQueryRequest(BaseModel):
    question: str
    metrics: list[str] = Field(default_factory=list)
    dimensions: list[str] = Field(default_factory=list)
    date_range: DateRange | None = None
    filters: dict[str, Any] = Field(default_factory=dict)
    limit: int = 100


class MarketingQueryResult(BaseModel):
    sql: str
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    source_tables: list[str] = Field(default_factory=list)


class PlannedQuery(BaseModel):
    question: str
    metrics: list[str] = Field(default_factory=list)
    dimensions: list[str] = Field(default_factory=list)
    date_range: DateRange | None = None
    filters: dict[str, Any] = Field(default_factory=dict)
    source_datasets: list[str] = Field(default_factory=list)
    limit: int = 100
    notes: list[str] = Field(default_factory=list)


class VisualSuggestion(BaseModel):
    type: str
    x_axis: str | None = None
    y_axis: list[str] = Field(default_factory=list)
    title: str | None = None


class MarketingAnswer(BaseModel):
    answer_markdown: str
    summary: str
    suggested_visual: str | VisualSuggestion | None = None
    suggested_followups: list[str] = Field(default_factory=list)
    generation_mode: str = "fallback"
    query_result: MarketingQueryResult | None = None
