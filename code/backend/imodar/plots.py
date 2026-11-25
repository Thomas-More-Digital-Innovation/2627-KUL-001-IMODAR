"""Deterministic renderer for LLM-chosen plot specifications.

The LLM (see ``plot_planner``) only emits a *spec*: plot type + column names.
This module validates every spec against the real DataFrame and draws it, so a
hallucinated column or impossible plot is rejected instead of drawn.
"""

from __future__ import annotations

import io
import threading
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402

PLOT_TYPES = ["bar", "box", "violin", "hist", "scatter", "line", "heatmap", "clustermap", "volcano", "kaplan_meier"]
MAX_HUE = 12
MAX_MATRIX_SIDE = 300
# pyplot keeps global state, while the API serves requests from several threads.
_PYPLOT_LOCK = threading.Lock()


@dataclass
class PlotSpec:
    type: str
    x: str | None = None
    y: str | None = None
    hue: str | None = None
    value: str | None = None  # heatmap / clustermap cell values
    title: str = ""
    rationale: str = ""
    log_y: bool = False

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> PlotSpec:
        def s(k):
            v = d.get(k)
            return v if isinstance(v, str) and v.strip() and v.lower() not in ("none", "null") else None

        return cls(
            type=str(d.get("type", "")).lower(),
            x=s("x"),
            y=s("y"),
            hue=s("hue"),
            value=s("value"),
            title=str(d.get("title") or ""),
            rationale=str(d.get("rationale") or ""),
            log_y=bool(d.get("log_y", False)),
        )


def _is_num(df: pd.DataFrame, c: str | None) -> bool:
    return c is not None and pd.api.types.is_numeric_dtype(df[c]) and not pd.api.types.is_bool_dtype(df[c])


def _is_event(s: pd.Series) -> bool:
    v = s.dropna()
    if len(v) == 0:
        return False
    if pd.api.types.is_bool_dtype(v):
        return True
    return pd.api.types.is_numeric_dtype(v) and set(v.unique()) <= {0, 1}


def kaplan_meier(time: np.ndarray, event: np.ndarray):
    """Kaplan-Meier estimator. Returns (t, S, lo, hi, censor_t, censor_S) with Greenwood 95% CI."""
    time, event = np.asarray(time, float), np.asarray(event, int)
    ts, surv, lo, hi = [0.0], [1.0], [1.0], [1.0]
    s, var_sum = 1.0, 0.0
    for t in np.unique(time[event == 1]):
        at_risk = (time >= t).sum()
        d = ((time == t) & (event == 1)).sum()
        s *= 1 - d / at_risk
        if at_risk > d:
            var_sum += d / (at_risk * (at_risk - d))
        se = s * np.sqrt(var_sum)
        ts.append(t)
        surv.append(s)
        lo.append(max(0.0, s - 1.96 * se))
        hi.append(min(1.0, s + 1.96 * se))
    ts, surv = np.array(ts), np.array(surv)
    cens = time[event == 0]
    cs = surv[np.searchsorted(ts, cens, side="right") - 1] if len(cens) else np.array([])
    return ts, surv, np.array(lo), np.array(hi), cens, cs


def logrank_p(time: np.ndarray, event: np.ndarray, group: np.ndarray) -> float | None:
    """Multi-group log-rank test p-value (None if < 2 groups or no events)."""
    from scipy.stats import chi2

    groups = list(pd.unique(group))
    k = len(groups)
    if k < 2:
        return None
    observed, expected, variance = np.zeros(k), np.zeros(k), np.zeros((k, k))
    for t in np.unique(time[event == 1]):
        at = time >= t
        n = at.sum()
        at_t = (time == t) & (event == 1)
        d = at_t.sum()
        nk = np.array([(at & (group == g)).sum() for g in groups], float)
        observed += np.array([(at_t & (group == g)).sum() for g in groups], float)
        expected += d * nk / n
        if n > 1:
            variance += d * (n - d) / (n - 1) / n * (np.diag(nk) - np.outer(nk, nk) / n)
    if observed.sum() == 0:
        return None
    diff = (observed - expected)[:-1]
    try:
        stat = float(diff @ np.linalg.solve(variance[:-1, :-1], diff))
    except np.linalg.LinAlgError:
        return None
    return float(chi2.sf(stat, k - 1))


def validate_spec(df: pd.DataFrame, spec: PlotSpec) -> str | None:
    """Return an error string if the spec can't be drawn from ``df``, else None."""
    if spec.type not in PLOT_TYPES:
        return f"unknown plot type '{spec.type}'"
    for name in (spec.x, spec.y, spec.hue, spec.value):
        if name is not None and name not in df.columns:
            return f"column '{name}' not in result"
    t = spec.type
    if t in ("bar", "box", "violin") and not (spec.x and _is_num(df, spec.y)):
        return f"{t} needs a categorical x and numeric y"
    if t == "hist" and not _is_num(df, spec.x):
        return "hist needs numeric x"
    if t == "scatter" and not (_is_num(df, spec.x) and _is_num(df, spec.y)):
        return "scatter needs numeric x and y"
    if t == "line" and not (spec.x and _is_num(df, spec.y)):
        return "line needs x and numeric y"
    if t in ("heatmap", "clustermap") and not (spec.x and spec.y and _is_num(df, spec.value)):
        return f"{t} needs x, y (categories) and numeric value"
    if t in ("heatmap", "clustermap") and max(df[spec.x].nunique(), df[spec.y].nunique()) > MAX_MATRIX_SIDE:
        return f"{t} has too many categories (> {MAX_MATRIX_SIDE})"
    if t == "volcano":
        if not (_is_num(df, spec.x) and _is_num(df, spec.y)):
            return "volcano needs numeric effect (x) and p-value (y)"
        if not df[spec.y].dropna().between(0, 1).all():
            return f"'{spec.y}' is not a p-value column (values outside 0-1)"
    if t == "kaplan_meier":
        if not _is_num(df, spec.x):
            return "kaplan_meier needs numeric time in x"
        if spec.y is None or not _is_event(df[spec.y]):
            return "kaplan_meier needs a binary event column (0/1 or boolean) in y"
        d = df[[spec.x, spec.y]].dropna()
        if len(d) < 2 or (d[spec.x] < 0).any():
            return "kaplan_meier needs >=2 rows with non-negative times"
    if spec.hue and df[spec.hue].nunique() > MAX_HUE:
        return f"hue '{spec.hue}' has too many levels (> {MAX_HUE})"
    if spec.x and t in ("bar", "box", "violin") and df[spec.x].nunique() > 60:
        return f"x '{spec.x}' has too many categories"
    return None


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Make a result plottable: unique columns, and DuckDB decimals as floats."""
    df = df.loc[:, ~df.columns.duplicated()].copy()
    for column in df.columns:
        values = df[column].dropna()
        if len(values) and all(isinstance(value, Decimal) for value in values):
            df[column] = df[column].astype(float)
    return df


def render_png(df: pd.DataFrame, spec: PlotSpec) -> bytes:
    """Draw a spec to PNG. Raises ValueError if the spec is invalid."""
    # Titles and columns are data: a "$" must not start a formula.
    with _PYPLOT_LOCK, matplotlib.rc_context({"text.parse_math": False}):
        try:
            buffer = io.BytesIO()
            draw(df, spec).savefig(buffer, format="png", dpi=130, bbox_inches="tight")
            return buffer.getvalue()
        finally:
            plt.close("all")


def draw(df: pd.DataFrame, spec: PlotSpec):
    """Draw a validated spec. Raises ValueError if invalid."""
    err = validate_spec(df, spec)
    if err:
        raise ValueError(err)
    sns.set_theme(style="whitegrid")
    t, x, y, hue = spec.type, spec.x, spec.y, spec.hue
    fig, ax = plt.subplots(figsize=(8, 4.8))

    if t == "bar":
        sns.barplot(data=df, x=x, y=y, hue=hue, errorbar="sd", ax=ax)
    elif t == "box":
        sns.boxplot(data=df, x=x, y=y, hue=hue, showfliers=False, ax=ax)
        if len(df) <= 500:
            sns.stripplot(
                data=df,
                x=x,
                y=y,
                hue=hue,
                dodge=bool(hue),
                color=None if hue else "black",
                alpha=0.5,
                size=3,
                legend=False,
                ax=ax,
            )
    elif t == "violin":
        sns.violinplot(data=df, x=x, y=y, hue=hue, inner="quartile", cut=0, ax=ax)
    elif t == "hist":
        sns.histplot(data=df, x=x, hue=hue, kde=len(df) > 5, ax=ax)
    elif t == "scatter":
        sns.scatterplot(data=df, x=x, y=y, hue=hue, ax=ax)
        if len(df) >= 3:
            sns.regplot(data=df, x=x, y=y, scatter=False, color="grey", ax=ax)
    elif t == "line":
        sns.lineplot(data=df, x=x, y=y, hue=hue, marker="o", errorbar="sd", ax=ax)
    elif t == "heatmap":
        pivot = df.pivot_table(index=y, columns=x, values=spec.value, aggfunc="mean")
        sns.heatmap(pivot, annot=pivot.size <= 200, fmt=".3g", cmap="viridis", ax=ax)
    elif t == "clustermap":
        plt.close(fig)
        pivot = df.pivot_table(index=y, columns=x, values=spec.value, aggfunc="mean")
        pivot = pivot.dropna(how="all").dropna(axis=1, how="all")
        if pivot.shape[0] < 2 or pivot.shape[1] < 2:
            raise ValueError("clustermap needs at least a 2x2 matrix")
        g = sns.clustermap(pivot.fillna(pivot.stack().mean()), z_score=0, cmap="vlag", center=0, figsize=(8, 7))
        if spec.title:
            g.figure.suptitle(spec.title, y=1.02)
        return g.figure
    elif t == "kaplan_meier":
        d = df.dropna(subset=[x, y] + ([hue] if hue else []))
        ev = d[y].astype(int).to_numpy()
        tm = d[x].astype(float).to_numpy()
        levels = list(pd.unique(d[hue])) if hue else [None]
        for lv in levels:
            m = np.ones(len(d), bool) if lv is None else (d[hue] == lv).to_numpy()
            ts, sv, lo, hi, ct, cs = kaplan_meier(tm[m], ev[m])
            label = "All" if lv is None else str(lv)
            line = ax.step(ts, sv, where="post", label=f"{label} (n={m.sum()}, events={ev[m].sum()})")[0]
            ax.fill_between(ts, lo, hi, step="post", alpha=0.15, color=line.get_color())
            ax.plot(ct, cs, "|", color=line.get_color(), ms=8)
        if hue and len(levels) >= 2:
            p = logrank_p(tm, ev, d[hue].to_numpy())
            if p is not None:
                ax.text(0.98, 0.98, f"log-rank p = {p:.3g}", transform=ax.transAxes, ha="right", va="top")
        ax.set_ylim(0, 1.05)
        ax.set_xlabel(x)
        ax.set_ylabel("Survival probability")
        ax.legend(loc="lower left")
    elif t == "volcano":
        p = df[y].astype(float).clip(lower=1e-300)
        sig = (p < 0.05) & (df[x].abs() >= 1)
        ax.scatter(df[x], -np.log10(p), c=np.where(sig, "crimson", "lightgrey"), s=14)
        ax.axhline(-np.log10(0.05), ls="--", c="grey", lw=0.8)
        for v in (-1, 1):
            ax.axvline(v, ls="--", c="grey", lw=0.8)
        ax.set_ylabel(f"-log10({y})")

    if spec.log_y and t not in ("heatmap", "volcano"):
        ax.set_yscale("log")
    if t in ("bar", "box", "violin"):
        ax.tick_params(axis="x", rotation=45)
        for lbl in ax.get_xticklabels():
            lbl.set_ha("right")
    if spec.title:
        ax.set_title(spec.title)
    fig.tight_layout()
    return fig
