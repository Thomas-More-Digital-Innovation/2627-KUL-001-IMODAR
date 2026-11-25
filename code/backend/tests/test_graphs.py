from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from imodar.plot_planner import create_graphs
from imodar.plots import PLOT_TYPES, PlotSpec, kaplan_meier, logrank_p, prepare, render_png, validate_spec

DATA = pd.DataFrame(
    {
        "group": ["a", "a", "a", "b", "b", "b"],
        "item": ["x", "y", "z"] * 2,
        "n": [1.0, 2.0, 4.0, 3.0, 1.5, 6.0],
        "m": [2.0, 3.0, 1.0, 5.0, 4.0, 2.5],
        "p": [0.01, 0.2, 0.5, 0.04, 0.9, 0.001],
        "event": [1, 0, 1, 1, 1, 0],
    }
)
FIELDS = {
    "hist": {"x": "n"},
    "scatter": {"x": "n", "y": "m"},
    "line": {"x": "item", "y": "n"},
    "heatmap": {"x": "item", "y": "group", "value": "n"},
    "clustermap": {"x": "item", "y": "group", "value": "n"},
    "volcano": {"x": "n", "y": "p"},
    "kaplan_meier": {"x": "n", "y": "event", "hue": "group"},
}


class StubModel:
    def __init__(self, *plots, fail=False):
        self.plots, self.fail = list(plots), fail

    def chat_json(self, messages, **options):
        self.options = options
        if self.fail:
            raise RuntimeError("http://internal-host refused")
        return {"plots": self.plots}


@pytest.mark.parametrize("kind", PLOT_TYPES)
def test_every_type_renders(kind):
    png = render_png(DATA, PlotSpec(kind, title="Cost $x_ {", **FIELDS.get(kind, {"x": "group", "y": "n"})))
    assert png.startswith(b"\x89PNG") and not plt.get_fignums()


def test_rendering_is_thread_safe():
    specs = [PlotSpec("bar", x="group", y="n"), PlotSpec("hist", x="n")] * 6
    with ThreadPoolExecutor(6) as pool:
        images = list(pool.map(lambda spec: render_png(DATA, spec), specs))
    assert len({*images[::2]}) == 1 and len({*images[1::2]}) == 1


@pytest.mark.parametrize(
    "spec",
    [
        PlotSpec("pie", x="group"),
        PlotSpec("bar", x="invented", y="n"),
        PlotSpec("scatter", x="group", y="n"),
        PlotSpec("volcano", x="p", y="n"),
        PlotSpec("kaplan_meier", x="n", y="m"),
    ],
)
def test_impossible_specs_are_rejected(spec):
    assert validate_spec(DATA, spec)


def test_huge_matrix_is_rejected():
    df = pd.DataFrame({"x": range(301), "y": ["a"] * 301, "v": 1.0})
    assert "too many" in validate_spec(df, PlotSpec("heatmap", x="x", y="y", value="v"))


def test_prepare_converts_decimals_and_drops_duplicate_columns():
    df = pd.DataFrame([[Decimal("1.5"), "a", 1], [None, "b", 2]], columns=["d", "t", "t"])
    prepared = prepare(df)
    assert list(prepared.columns) == ["d", "t"] and prepared.d.dtype == float


def test_survival_statistics():
    times, survival, *_ = kaplan_meier([1, 2, 3, 4], [1, 0, 1, 1])
    assert list(times) == [0, 1, 3, 4] and np.allclose(survival, [1, 0.75, 0.375, 0])
    same = np.array([1.0, 2, 3, 1, 2, 3])
    assert logrank_p(same, np.ones(6), np.array(list("aaabbb"))) == pytest.approx(1)


def test_valid_graphs_survive_invalid_ones_and_use_thinking():
    model = StubModel({"type": "bar", "x": "group", "y": "n"}, {"type": "bar", "x": "nope", "y": "n"}, "junk")
    result = create_graphs(model, "q", DATA, "SELECT 1")
    assert (len(result.graphs), len(result.rejected)) == (1, 1) and model.options["think"] is True


def test_model_failure_does_not_leak_or_raise():
    result = create_graphs(StubModel(fail=True), "q", DATA, "SELECT 1")
    assert result.error and "internal-host" not in result.error


def test_drawing_failure_is_reported(monkeypatch):
    monkeypatch.setattr("imodar.plot_planner.render_png", lambda *_: 1 / 0)
    result = create_graphs(StubModel({"type": "hist", "x": "n"}), "q", DATA, "SELECT 1")
    assert not result.graphs and len(result.rejected) == 1


def test_empty_result_skips_the_model():
    model = StubModel()
    assert create_graphs(model, "q", DATA.head(0), "SELECT 1").graphs == [] and not hasattr(model, "options")
