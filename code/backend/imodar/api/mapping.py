"""Maps pipeline results onto the HTTP contracts."""

import json

from ..engine import ExecResult
from ..pipeline import PipelineResult
from .contracts import AnalysisResponse, AuditTrail, GuardCheck, ResolvedEntity, ResultTable


def _table(result: ExecResult | None) -> ResultTable | None:
    if result is None or result.df is None:
        return None
    # pandas' encoder maps NaN, dates, decimals and numpy scalars, which the json module rejects.
    data = json.loads(result.df.to_json(orient="split", date_format="iso", double_precision=15))["data"]
    return ResultTable(
        columns=[str(column) for column in result.df.columns],
        rows=data,
        row_count=result.row_count,
        truncated=result.truncated,
        elapsed_ms=result.elapsed_ms,
    )


def _entities(result: PipelineResult) -> list[ResolvedEntity]:
    entities = []
    for resolution in result.resolutions:
        for hit in resolution.concepts:
            entities.append(
                ResolvedEntity(
                    mention=resolution.mention,
                    resolved_to=hit.concept_name,
                    concept_id=hit.concept_id,
                    domain=hit.domain_id,
                    score=hit.score,
                    source=hit.source,
                    studies=sorted({item["study_id"] for item in hit.coverage}),
                )
            )
        for value in resolution.values:
            entities.append(
                ResolvedEntity(
                    mention=resolution.mention,
                    resolved_to=f"{value.table_column} = '{value.value}'",
                    concept_id=value.concept_id,
                    domain="Categorical value",
                    score=value.score,
                    source=value.source,
                    studies=[],
                )
            )
    return entities


def to_response(result: PipelineResult) -> AnalysisResponse:
    """Expose a pipeline result together with everything needed to audit it."""
    checks = result.guard_report.checks if result.guard_report else []
    return AnalysisResponse(
        question=result.question,
        status=result.status,
        summary=result.synthesis,
        elapsed_ms=result.total_elapsed_ms,
        table=_table(result.exec_result),
        audit=AuditTrail(
            reasoning=result.plan_reasoning,
            data_sources=result.data_sources,
            sql=result.sql,
            entities=_entities(result),
            checks=[GuardCheck(name=name, passed=passed, detail=detail) for name, passed, detail in checks],
            attempts=len(result.attempts),
        ),
    )
