"""Factual Synthesis: generates verifiable prose strictly anchored to the query result table."""

from __future__ import annotations

import pandas as pd

from . import config
from .llm import OllamaClient

SYNTHESIS_SYSTEM_PROMPT = """You are a strictly factual medical report synthesizer.
Your task is to summarize the analytical query results for the user's question.

CRITICAL CONSTRAINTS:
1. STRICT ZERO-HALLUCINATION POLICY: You must ONLY present the exact values, counts, categories, and metrics shown in the provided Result Data Table.
2. DO NOT make up or extrapolate numbers, statistics, or biological implications not present in the table.
3. If the table is empty (0 rows), state plainly that no matching records were found in the database.
4. Reference the studies, cohorts, or patient counts by name and number exactly as returned.
5. Format key figures and comparisons in clean, readable markdown (bullet points or brief paragraphs).
"""


class Synthesizer:
    def __init__(self, llm: OllamaClient):
        self.llm = llm

    def synthesize(
        self,
        question: str,
        sql: str,
        df: pd.DataFrame | None,
        total_rows: int,
        max_rows_for_prompt: int = config.SYNTH_MAX_ROWS,
    ) -> str:
        if df is None or len(df) == 0:
            return "No matching records were found in the warehouse for this query."

        # Prepare table preview
        rows_to_show = df.head(max_rows_for_prompt)
        try:
            table_md = rows_to_show.to_markdown(index=False)
        except Exception:
            table_md = rows_to_show.to_string(index=False)
        trunc_note = (
            f"\n*(Showing top {len(rows_to_show)} of {total_rows} total rows)*"
            if total_rows > len(rows_to_show)
            else ""
        )

        user_prompt = f"""User Question:
"{question}"

Executed SQL Query:
```sql
{sql}
```

Result Data Table:
{table_md}{trunc_note}

Summarize the key facts answering the question based strictly and exclusively on the table above.
"""

        messages = [
            {"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        try:
            return self.llm.chat(messages, temperature=0.0)
        except RuntimeError:
            return "(Could not generate synthesis prose. Please inspect the raw data table below.)"
