"""FastAPI composition root. Run with: uv run uvicorn imodar.api.main:app"""

import logging
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException

from ..engine import Warehouse
from ..pipeline import Pipeline
from .contracts import AnalysisRequest, AnalysisResponse, HealthResponse, Study
from .mapping import to_response

logger = logging.getLogger(__name__)

# TODO: add authentication and per-study authorisation before exposing this beyond localhost.
app = FastAPI(title="IMODAR API", version="0.1.0")


@lru_cache
def _warehouse() -> Warehouse:
    return Warehouse()


@lru_cache
def _pipeline() -> Pipeline:
    return Pipeline(wh=_warehouse())


def get_warehouse() -> Warehouse:
    try:
        return _warehouse()
    except FileNotFoundError as error:
        logger.exception("Warehouse unavailable")
        raise HTTPException(503, "The data warehouse is unavailable.") from error


def get_pipeline(_: Annotated[Warehouse, Depends(get_warehouse)]) -> Pipeline:
    try:
        return _pipeline()
    except RuntimeError as error:
        logger.exception("Terminology service unavailable")
        raise HTTPException(503, "The terminology service is unavailable.") from error


@app.get("/api/health")
def health() -> HealthResponse:
    """Liveness only; does not touch the warehouse or the model."""
    return HealthResponse(status="ok")


@app.get("/api/studies", responses={503: {"description": "Warehouse unavailable"}})
def list_studies(warehouse: Annotated[Warehouse, Depends(get_warehouse)]) -> list[Study]:
    """List the studies that contain queryable data."""
    frame = warehouse.query_df(
        "SELECT study_id, study_name, coalesce(n_participants, 0) AS n_participants, "
        "coalesce(CAST(modalities AS VARCHAR), '') AS modalities "
        "FROM catalog.studies WHERE has_data ORDER BY study_id"
    )
    return [Study.model_validate(row) for row in frame.to_dict("records")]


@app.post("/api/analyses", responses={503: {"description": "A dependency is unavailable"}})
def create_analysis(request: AnalysisRequest, pipeline: Annotated[Pipeline, Depends(get_pipeline)]) -> AnalysisResponse:
    """Plan, validate, execute and summarise a question."""
    question = request.question.strip()
    if not question:
        raise HTTPException(422, "The question must not be blank.")
    try:
        return to_response(pipeline.run(question))
    except RuntimeError as error:
        logger.exception("Analysis dependency failed")
        raise HTTPException(503, "The analysis service is unavailable.") from error
