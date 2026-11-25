"""End-to-end multi-stage pipeline coordinator."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from .concepts import ConceptIndex, Resolution
from .engine import ExecResult, Warehouse
from .guard import GuardReport
from .llm import OllamaClient
from .planner import PlanAttempt, PlanResult, QueryPlanner
from .synthesizer import Synthesizer


@dataclass
class PipelineResult:
    question: str
    status: str  # "ok" | "clarify" | "error"
    resolutions: list[Resolution]
    plan_reasoning: str
    data_sources: list[str]
    sql: str
    guard_report: GuardReport | None
    exec_result: ExecResult | None
    synthesis: str
    total_elapsed_ms: float
    attempts: list[PlanAttempt] = field(default_factory=list)
    error_message: str | None = None


class Pipeline:
    def __init__(
        self,
        wh: Warehouse | None = None,
        llm: OllamaClient | None = None,
        concept_index: ConceptIndex | None = None,
    ):
        self.wh = wh or Warehouse()
        self.llm = llm or OllamaClient()
        self.concept_index = concept_index or ConceptIndex(self.wh)
        self.planner = QueryPlanner(self.wh, self.llm, self.concept_index)
        self.synthesizer = Synthesizer(self.llm)

    def run(self, question: str, synthesize_prose: bool = True, think: bool | None = None) -> PipelineResult:
        t0 = time.perf_counter()

        # Run planner (which includes semantic resolution, guardrail validation, and execution)
        plan: PlanResult = self.planner.plan_query(question, think=think)

        if plan.status == "clarify":
            total_elapsed = (time.perf_counter() - t0) * 1000
            return PipelineResult(
                question=question,
                status="clarify",
                resolutions=plan.resolutions,
                plan_reasoning=plan.reasoning_steps,
                data_sources=plan.data_sources,
                sql="",
                guard_report=None,
                exec_result=None,
                synthesis=plan.clarification_message or plan.reasoning_steps,
                total_elapsed_ms=total_elapsed,
                attempts=plan.attempts,
            )

        if plan.status == "failed" or plan.exec_result is None or plan.exec_result.error is not None:
            total_elapsed = (time.perf_counter() - t0) * 1000
            err_msg = plan.clarification_message or (plan.exec_result.error if plan.exec_result else "Planning failed")
            return PipelineResult(
                question=question,
                status="error",
                resolutions=plan.resolutions,
                plan_reasoning=plan.reasoning_steps,
                data_sources=plan.data_sources,
                sql=plan.sql,
                guard_report=plan.guard_report,
                exec_result=plan.exec_result,
                synthesis=f"Error executing query: {err_msg}",
                total_elapsed_ms=total_elapsed,
                attempts=plan.attempts,
                error_message=err_msg,
            )

        # Successful execution -> synthesize factual summary
        synthesis_text = ""
        if synthesize_prose and plan.exec_result.df is not None:
            synthesis_text = self.synthesizer.synthesize(
                question=question,
                sql=plan.sql,
                df=plan.exec_result.df,
                total_rows=plan.exec_result.row_count,
                think=think,
            )

        total_elapsed = (time.perf_counter() - t0) * 1000

        return PipelineResult(
            question=question,
            status="ok",
            resolutions=plan.resolutions,
            plan_reasoning=plan.reasoning_steps,
            data_sources=plan.data_sources,
            sql=plan.sql,
            guard_report=plan.guard_report,
            exec_result=plan.exec_result,
            synthesis=synthesis_text,
            total_elapsed_ms=total_elapsed,
            attempts=plan.attempts,
        )
