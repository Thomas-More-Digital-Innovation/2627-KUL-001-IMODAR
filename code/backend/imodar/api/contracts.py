"""Public HTTP contracts; the frontend types are generated from these models."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok"]


class Study(BaseModel):
    study_id: str
    study_name: str
    n_participants: int
    modalities: str


class AnalysisRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class ResultTable(BaseModel):
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    truncated: bool
    elapsed_ms: float


class ResolvedEntity(BaseModel):
    mention: str
    resolved_to: str
    concept_id: int | None
    domain: str
    score: float
    source: str
    studies: list[str]


class GuardCheck(BaseModel):
    name: str
    passed: bool
    detail: str


class AuditTrail(BaseModel):
    reasoning: str
    data_sources: list[str]
    sql: str
    entities: list[ResolvedEntity]
    checks: list[GuardCheck]
    attempts: int


class AnalysisResponse(BaseModel):
    question: str
    status: Literal["ok", "clarify", "error"]
    summary: str
    elapsed_ms: float
    table: ResultTable | None
    audit: AuditTrail
