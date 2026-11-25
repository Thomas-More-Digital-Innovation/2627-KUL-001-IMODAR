"""Query Planner: leverages Ollama with strict schema prompt injection and self-correction."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from . import config
from .concepts import ConceptHit, ConceptIndex, Resolution, ValueHit, candidate_mentions
from .engine import ExecResult, Warehouse
from .guard import GuardReport, validate
from .llm import OllamaClient
from .schema_docs import TABLES

PLANNER_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["ok", "clarify"],
            "description": "'ok' if a deterministic query can be planned; 'clarify' if key entities are ambiguous or data is missing.",
        },
        "reasoning_steps": {
            "type": "string",
            "description": "Step-by-step logic explaining the data flow, joins, and filters.",
        },
        "data_sources": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of tables or views queried, e.g. ['catalog.studies', 'omop.measurement']",
        },
        "query": {
            "type": "string",
            "description": "Valid, read-only DuckDB SQL query string (empty if status is clarify).",
        },
        "clarification_message": {
            "type": "string",
            "description": "Question or explanation if status is clarify.",
        },
    },
    "required": ["status", "reasoning_steps", "data_sources", "query"],
}


@dataclass
class PlanAttempt:
    attempt: int
    raw_response: dict[str, Any]
    guard_report: GuardReport | None = None
    exec_result: ExecResult | None = None
    feedback_to_llm: str | None = None


@dataclass
class PlanResult:
    status: str  # "ok" | "clarify" | "failed"
    question: str
    resolutions: list[Resolution]
    reasoning_steps: str
    data_sources: list[str]
    sql: str
    guard_report: GuardReport | None
    exec_result: ExecResult | None
    clarification_message: str | None = None
    attempts: list[PlanAttempt] = field(default_factory=list)


def format_schema_prompt(wh: Warehouse, value_profiles: dict[str, list]) -> str:
    """Build a concise, structured markdown representation of tables, columns, and data types."""
    lines: list[str] = ["### Warehouse Schema & Tables:"]
    for full_name, table_info in TABLES.items():
        schema_name, tbl_name = full_name.split(".", 1)
        actual_cols = wh.schema.get(schema_name, {}).get(tbl_name, {})
        lines.append(f"\n#### Table: `{full_name}`")
        lines.append(f"Description: {table_info.get('doc', '')}")
        lines.append("Columns:")
        for col, doc in table_info.get("columns", {}).items():
            dtype = actual_cols.get(col, "UNKNOWN")
            vp = value_profiles.get(f"{full_name}.{col}")
            sample = f" [Allowed values: {', '.join(repr(v) for v in vp[:12])}]" if vp else ""
            lines.append(f"  - `{col}` ({dtype}): {doc}{sample}")
    return "\n".join(lines)


def format_concepts_prompt(resolutions: list[Resolution]) -> str:
    """Render resolved semantic entities, OMOP concept IDs, value sets, and study coverage."""
    if not resolutions:
        return "No specific medical concepts matched automatically. You may query `omop.concept` or `catalog.concept_coverage` if needed."

    lines: list[str] = ["### Resolved Semantic Entities & Concept Mappings:"]
    lines.append("Use these verified Concept IDs in your SQL WHERE clauses (never fabricate concept IDs):")

    for res in resolutions:
        lines.append(f'\nMention in question: "{res.mention}"')
        if res.concepts:
            for c in res.concepts:

                def _safe_part(prefix: str, val: Any) -> str:
                    if val is None or pd.isna(val) or not str(val).strip():
                        return ""
                    return f"{prefix}{val}"

                parts = []
                for cv in c.coverage:
                    m = _safe_part(", ", cv.get("modality"))
                    u = _safe_part(", unit=", cv.get("units"))
                    vt = _safe_part(", val_type=", cv.get("value_types"))
                    parts.append(
                        f"Study {cv.get('study_id')} ({cv.get('source_table')}{m}{u}{vt}, N={cv.get('n_persons')})"
                    )
                cov_str = "; ".join(parts) or "No recorded occurrences"
                lines.append(f'  - Concept ID: `{c.concept_id}` -> "{c.concept_name}" (Domain: {c.domain_id})')
                lines.append(f"    Coverage: {cov_str}")
                if c.values:
                    lines.append(f"    Available observation values: {', '.join(repr(v) for v in c.values[:10])}")
                if c.descendants:
                    desc_str = ", ".join(f"`{d[0]}` ({d[1]})" for d in c.descendants[:8])
                    lines.append(f"    Subtypes / descendants: {desc_str}")
        if res.values:
            for v in res.values:
                lines.append(f"  - Exact Value: column `{v.table_column}` = '{v.value}' (match score: {v.score:.0f})")

    return "\n".join(lines)


SYSTEM_PROMPT = """You are a deterministic Medical Data Query Planner and Translator.
Your job is to translate a user's natural language question into a single, highly accurate, read-only DuckDB SQL query.

CRITICAL ARCHITECTURAL CONSTRAINTS:
1. PURE QUERY PLANNER: You NEVER execute queries, fabricate numbers, or calculate estimates in your thoughts. The analytical database (DuckDB) executes the query.
2. STRICT READ-ONLY SQL: Only generate SELECT statements (including WITH clauses). No INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, PRAGMA, COPY, or file functions.
3. PREVENT HALLUCINATIONS:
   - Use ONLY explicit tables and columns from the provided schema metadata.
   - Use ONLY verified concept IDs provided in the 'Resolved Semantic Entities' section, or write a subquery against `omop.concept` / `omop.concept_ancestor`.
   - Never guess SNOMED / LOINC / OMOP IDs.
4. MODELING RULES:
   - All numeric values (lab tests, cytokines, intensities, BMI, etc.) are stored in `omop.measurement` (long format).
   - In `omop.measurement`, check `value_type` when relevant (e.g. 'concentration' for Luminex cytokines, 'log2_intensity' or 'intensity' for mass spec).
   - `value_as_number` is NULL for out-of-range readings (< or > limit of detection).
   - All categorical clinical facts (smoking, staging, MGMT, IDH, chemo response, comorbidities) are in `omop.observation` (long format) with `value_as_string`.
   - Primary cancer diagnosis is in `omop.condition_occurrence`. Note that healthy controls in case-control studies have no condition row.
   - When filtering conditions, if subtypes/descendants are listed in the 'Resolved Semantic Entities' section, include them in an IN (...) clause (e.g. `condition_concept_id IN (<parent_id>, <descendant_id>)`) or join with `omop.concept_ancestor` to capture patients diagnosed with specific subtypes (e.g. Epithelial ovarian cancer).
   - For study-level inquiries, check `catalog.studies` or `catalog.concept_coverage`.
   - For tumour genomics (driver genes, VAF, CNV, fusions), check `genomics.ngs_variant`.
   - For radiology and imaging data (scans, DICOM series, modalities like CT, PET/PT, RTSTRUCT, slice counts, scanner manufacturers/models), check `imaging.radiology_series`.
5. AMBIGUITY / CLARIFICATION:
   - If an entity, metric, or study requested by the user is not present in the warehouse, or if the intent is fundamentally ambiguous, set status="clarify" and provide a clear explanation in `clarification_message`.
   - Do NOT assume arbitrary filters if not specified.
6. SURVIVAL / KAPLAN-MEIER QUESTIONS (when the user asks about survival, PFS, OS or a Kaplan-Meier curve):
   - Return ONE ROW PER PATIENT (never aggregate), with these exact column aliases:
     `person_id`, `study_id`, `time_months` (the survival duration from `omop.measurement.value_as_number`),
     `event` (1 = event observed, 0 = censored) and, if the user wants groups, a `group_label` column
     (e.g. cancer type from `omop.concept.concept_name` joined via `omop.condition_occurrence.condition_concept_id`,
     MGMT status from `omop.observation.value_as_string`, study_id, or cohort_group).
   - Choose the studies yourself: use the survival concept coverage (Overall survival / Progression-free survival) from the
     'Resolved Semantic Entities' section and include every study that has it, unless the user restricts the scope.
   - The warehouse has NO vital-status or censoring flag. Therefore: for overall survival use `1 AS event` (every recorded
     duration is treated as an observed event). For progression-free survival use the `Recurrence` observation when it exists
     (`CASE WHEN rec.value_as_string = 'No' THEN 0 ELSE 1 END AS event`, LEFT JOIN on person_id), otherwise `1 AS event`.
   - You MUST state this event assumption explicitly in your plan reasoning so the user can see it.
   - Exclude persons without a survival measurement. Do not return a Kaplan-Meier question as a count or average.
7. DUCKDB DIALECT:
   - DuckDB supports standard SQL, CTEs (`WITH ...`), `ROUND(...)`, `COUNT(DISTINCT ...)`, string aggregations `string_agg(...)`, and case-insensitive comparison (`ILIKE`).
"""


class QueryPlanner:
    def __init__(self, wh: Warehouse, llm: OllamaClient, concept_index: ConceptIndex):
        self.wh = wh
        self.llm = llm
        self.concept_index = concept_index
        self.value_profiles = wh.value_profile()
        self.known_concepts = set(wh.query_df("SELECT concept_id FROM omop.concept").concept_id.astype(int))
        self.schema_prompt = format_schema_prompt(wh, self.value_profiles)

    def extract_and_resolve(self, question: str) -> list[Resolution]:
        """Resolve mentions in the question using candidate n-grams against the concept index."""
        candidates = candidate_mentions(question)
        resolutions = self.concept_index.resolve(candidates)
        # Keep resolutions that actually found a concept or value
        meaningful = [r for r in resolutions if r.concepts or r.values]
        return meaningful

    def plan_query(
        self,
        question: str,
        max_attempts: int = config.MAX_PLAN_ATTEMPTS,
        temperature: float = 0.0,
        think: bool | None = None,
    ) -> PlanResult:
        # Step 1: Semantic Entity Resolution
        resolutions = self.extract_and_resolve(question)
        concepts_prompt = format_concepts_prompt(resolutions)

        # Initial prompt
        user_prompt = f"""User Question:
"{question}"

{concepts_prompt}

{self.schema_prompt}

Generate a deterministic execution plan and SQL query formatted as the required JSON schema.
"""

        messages: list[dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        attempts: list[PlanAttempt] = []

        for attempt_idx in range(1, max_attempts + 1):
            raw_json = self.llm.chat_json(
                messages, json_schema=PLANNER_JSON_SCHEMA, temperature=temperature, think=think
            )
            attempt = PlanAttempt(attempt=attempt_idx, raw_response=raw_json)
            attempts.append(attempt)

            status = raw_json.get("status", "ok")
            reasoning = raw_json.get("reasoning_steps", "")
            data_sources = raw_json.get("data_sources", [])
            query_str = (raw_json.get("query") or "").strip()
            clarification = raw_json.get("clarification_message")

            # If model requested clarification:
            if status == "clarify":
                return PlanResult(
                    status="clarify",
                    question=question,
                    resolutions=resolutions,
                    reasoning_steps=reasoning,
                    data_sources=data_sources,
                    sql="",
                    guard_report=None,
                    exec_result=None,
                    clarification_message=clarification or reasoning,
                    attempts=attempts,
                )

            # Step 2: AST Guardrail validation
            guard_report = validate(query_str, self.wh.schema, self.known_concepts)
            attempt.guard_report = guard_report

            if not guard_report.ok:
                feedback = (
                    "The SQL query you generated failed the AST Guardrail Validator with error(s):\n"
                    + "\n".join(f"- {err}" for err in guard_report.errors)
                    + "\nPlease fix the SQL query to strictly follow the DuckDB schema and read-only rules."
                )
                attempt.feedback_to_llm = feedback
                messages.append({"role": "assistant", "content": json.dumps(raw_json)})
                messages.append({"role": "user", "content": feedback})
                continue

            # Step 3: Local Dry-run / Execution Test
            exec_res = self.wh.execute(guard_report.sql)
            attempt.exec_result = exec_res

            if exec_res.error:
                feedback = (
                    f"The SQL query passed AST syntax checks but caused a DuckDB execution error:\n"
                    f"{exec_res.error}\n"
                    f"Please adjust column names, types, or joins and regenerate the plan."
                )
                attempt.feedback_to_llm = feedback
                messages.append({"role": "assistant", "content": json.dumps(raw_json)})
                messages.append({"role": "user", "content": feedback})
                continue

            # Both guardrail and execution succeeded
            return PlanResult(
                status="ok",
                question=question,
                resolutions=resolutions,
                reasoning_steps=reasoning,
                data_sources=data_sources,
                sql=guard_report.sql,
                guard_report=guard_report,
                exec_result=exec_res,
                clarification_message=None,
                attempts=attempts,
            )

        # Exhausted attempts
        last_attempt = attempts[-1]
        last_err = ""
        if last_attempt.guard_report and not last_attempt.guard_report.ok:
            last_err = "; ".join(last_attempt.guard_report.errors)
        elif last_attempt.exec_result and last_attempt.exec_result.error:
            last_err = last_attempt.exec_result.error

        return PlanResult(
            status="failed",
            question=question,
            resolutions=resolutions,
            reasoning_steps=last_attempt.raw_response.get("reasoning_steps", "Failed validation after retries"),
            data_sources=last_attempt.raw_response.get("data_sources", []),
            sql=last_attempt.raw_response.get("query", ""),
            guard_report=last_attempt.guard_report,
            exec_result=last_attempt.exec_result,
            clarification_message=f"Query generation failed after {max_attempts} attempts. Last issue: {last_err}",
            attempts=attempts,
        )
