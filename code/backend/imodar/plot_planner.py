"""LLM plot planner: picks plot types and columns for a query result.

The model sees the question, the column profile and a few sample rows (never the
full table) and returns a JSON list of specs. Specs are validated against the
DataFrame by ``plots.validate_spec`` before anything is drawn.
"""

from __future__ import annotations

import base64
import logging
from dataclasses import dataclass, field

import pandas as pd

from .llm import OllamaClient
from .plots import PLOT_TYPES, PlotSpec, prepare, render_png, validate_spec

logger = logging.getLogger(__name__)

PLOT_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "plots": {
            "type": "array",
            "maxItems": 3,
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": PLOT_TYPES},
                    "x": {"type": ["string", "null"]},
                    "y": {"type": ["string", "null"]},
                    "hue": {"type": ["string", "null"]},
                    "value": {"type": ["string", "null"]},
                    "title": {"type": "string"},
                    "rationale": {"type": "string"},
                    "log_y": {"type": "boolean"},
                },
                "required": ["type", "title", "rationale"],
            },
        }
    },
    "required": ["plots"],
}

SYSTEM_PROMPT = """You are a bioinformatics data-visualisation planner.
Given a user's question and a profile of the query result table, choose 0-3 plots that best
answer the question visually, as an experienced bioinformatician would.

Plot types and the columns they need (use ONLY column names from the profile):
- bar:       x=categorical, y=numeric (mean ± SD per group), optional hue
- box/violin: x=categorical group, y=numeric, optional hue. Best to compare distributions between groups.
- hist:      x=numeric (distribution), optional hue
- scatter:   x=numeric, y=numeric (relationship), optional hue
- line:      x=timepoint/ordered variable, y=numeric, optional hue (longitudinal data)
- heatmap:   x, y=categorical, value=numeric (matrix of values)
- clustermap: like heatmap but clustered (many proteins/genes x samples/groups)
- volcano:   x=effect size/log fold change, y=p-value (0-1)
- kaplan_meier: x=follow-up time column (numeric), y=binary event column (1=event e.g. progression/death, 0=censored),
                optional hue=group (e.g. MGMT status). Use for survival questions (PFS, OS). One row per patient.

Rules:
- Choose plots that answer THE QUESTION. Prefer 1 strong plot over 3 weak ones.
- Return an empty list if the table is not meaningfully plottable (e.g. a single row, or only text columns).
- Pre-aggregated counts per category -> bar with that count column as y.
- If the user asks for a Kaplan-Meier / survival curve and the table has a time column and a 0/1 event column
  (e.g. `time_months`, `event`), use kaplan_meier with hue = the group column (e.g. `group_label`).
- Never invent columns. Titles should be short and state what is shown, with units if known.
- rationale: one sentence on why this plot fits.
"""


def profile_df(df: pd.DataFrame, max_sample: int = 8) -> str:
    lines = [f"rows={len(df)}, columns={len(df.columns)}", "columns:"]
    for c in df.columns:
        s = df[c]
        n_unique = s.nunique(dropna=True)
        if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
            d = s.dropna()
            rng = f"min={d.min():.4g}, max={d.max():.4g}" if len(d) else "all null"
            lines.append(f"- {c} [numeric] unique={n_unique}, {rng}, nulls={int(s.isna().sum())}")
        else:
            top = ", ".join(map(str, s.dropna().astype(str).value_counts().head(6).index))
            lines.append(f"- {c} [categorical] unique={n_unique}, top values: {top}")
    lines.append("sample rows:")
    lines.append(df.head(max_sample).to_csv(index=False))
    return "\n".join(lines)


@dataclass
class PlotPlan:
    specs: list[PlotSpec] = field(default_factory=list)
    rejected: list[tuple[PlotSpec, str]] = field(default_factory=list)
    error: str | None = None
    raw: dict | None = None


def plan_plots(
    llm: OllamaClient, question: str, df: pd.DataFrame, think: bool = True, sql: str | None = None
) -> PlotPlan:
    """Ask the LLM (thinking mode by default) for plot specs and keep only valid ones."""
    if df is None or df.empty:
        return PlotPlan()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Question: {question}\n\n"
            + (f"SQL that produced the table:\n{sql}\n\n" if sql else "")
            + f"Result table profile:\n{profile_df(df)}",
        },
    ]
    try:
        raw = llm.chat_json(messages, json_schema=PLOT_JSON_SCHEMA, temperature=0.0, think=think)
    except RuntimeError:
        logger.exception("Graph planning failed")
        return PlotPlan(error="The graphs could not be planned.")

    plan = PlotPlan(raw=raw)
    for item in raw.get("plots", [])[:3]:
        if not isinstance(item, dict):
            continue
        spec = PlotSpec.from_dict(item)
        err = validate_spec(df, spec)
        if err:
            plan.rejected.append((spec, err))
        else:
            plan.specs.append(spec)
    return plan


@dataclass
class Graph:
    spec: PlotSpec
    png_base64: str


@dataclass
class GraphResult:
    graphs: list[Graph] = field(default_factory=list)
    rejected: list[tuple[PlotSpec, str]] = field(default_factory=list)
    error: str | None = None


def create_graphs(llm: OllamaClient, question: str, df: pd.DataFrame, sql: str) -> GraphResult:
    """Plan and draw graphs. Never raises for a bad graph, so the answer itself is always kept."""
    df = prepare(df)
    plan = plan_plots(llm, question, df, sql=sql)
    result = GraphResult(rejected=plan.rejected, error=plan.error)
    for spec in plan.specs:
        try:
            image = base64.b64encode(render_png(df, spec)).decode()
        except Exception:  # noqa: BLE001 - plotting libraries raise anything on unusual data
            logger.exception("Could not draw a %s graph", spec.type)
            result.rejected.append((spec, "the graph could not be drawn from this result"))
        else:
            result.graphs.append(Graph(spec, image))
    return result
