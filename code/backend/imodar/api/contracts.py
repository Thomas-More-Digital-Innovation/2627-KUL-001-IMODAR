"""Public HTTP contracts; the frontend types are generated from these models."""

from typing import Any, Literal

from pydantic import BaseModel, Field

from ..db.models import Role


class HealthResponse(BaseModel):
    status: Literal["ok"]


class Study(BaseModel):
    study_id: str
    study_name: str
    n_participants: int
    modalities: str


class AnalysisRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    think: bool | None = Field(default=None, description="Model thinking mode; null uses the server default.")
    graphs: bool = Field(default=False, description="Also let the model choose graphs for the result.")


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


class Graph(BaseModel):
    type: str
    title: str
    rationale: str
    png_base64: str


class RejectedGraph(BaseModel):
    type: str
    title: str
    reason: str


class GraphReport(BaseModel):
    items: list[Graph]
    rejected: list[RejectedGraph]
    error: str | None


class AnalysisResponse(BaseModel):
    question: str
    status: Literal["ok", "clarify", "error"]
    summary: str
    elapsed_ms: float
    table: ResultTable | None
    graphs: GraphReport | None = Field(description="Null when graphs were not requested or there is no result.")
    audit: AuditTrail


class LoginRequest(BaseModel):
    email: str = Field(max_length=320)
    password: str = Field(max_length=128)
    remember: bool = False


class LoginResponse(BaseModel):
    next: Literal["enrol", "verify"]


class CodeRequest(BaseModel):
    code: str = Field(min_length=6, max_length=32, pattern=r"^[0-9A-Za-z -]+$")


class EnrolmentResponse(BaseModel):
    secret: str
    qr_code: str


class RecoveryCodesResponse(BaseModel):
    recovery_codes: list[str]


class CurrentUser(BaseModel):
    email: str
    full_name: str
    role: Role


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(max_length=128)
    new_password: str = Field(min_length=12, max_length=128)
