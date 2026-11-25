import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from imodar.api.auth import require_user
from imodar.api.main import app, get_pipeline, get_warehouse
from imodar.concepts import ConceptHit, Resolution
from imodar.guard import validate
from imodar.pipeline import PipelineResult

SQL = "SELECT person_id, age_years FROM omop.person ORDER BY person_id"


class StubPipeline:
    def __init__(self, warehouse):
        self.warehouse = warehouse

    def run(self, question):
        if question == "offline":
            raise RuntimeError("http://internal-host refused")
        ok = question != "clarify"
        report = validate(SQL, self.warehouse.schema, set())
        return PipelineResult(
            question=question,
            status="ok" if ok else "clarify",
            resolutions=[Resolution("age", [ConceptHit(1, "Age", "Person", "age", 100, [{"study_id": "T-1"}])])],
            plan_reasoning="Read people",
            data_sources=["omop.person"],
            sql=report.sql if ok else "",
            guard_report=report if ok else None,
            exec_result=self.warehouse.execute(report.sql) if ok else None,
            synthesis="Two people.",
            total_elapsed_ms=1,
        )


@pytest.fixture
def client(warehouse):
    app.dependency_overrides[get_warehouse] = lambda: warehouse
    app.dependency_overrides[require_user] = lambda: None
    app.dependency_overrides[get_pipeline] = lambda: StubPipeline(warehouse)
    yield TestClient(app)
    app.dependency_overrides.clear()


def ask(client, question):
    return client.post("/api/analyses", json={"question": question})


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_lists_only_studies_with_data(client):
    assert [study["study_id"] for study in client.get("/api/studies").json()] == ["T-1"]


def test_analysis_includes_table_and_audit(client):
    body = ask(client, " ages ").json()
    assert body["question"] == "ages"
    assert body["table"]["rows"] == [[1, 50], [2, None]]
    assert body["audit"]["entities"][0]["studies"] == ["T-1"]
    assert all(check["passed"] for check in body["audit"]["checks"])


def test_clarification_has_no_table(client):
    body = ask(client, "clarify").json()
    assert body["status"] == "clarify" and body["table"] is None


@pytest.mark.parametrize("question", ["", "   ", "x" * 2001])
def test_rejects_invalid_question(client, question):
    assert ask(client, question).status_code == 422


def test_outage_does_not_leak_internals(client):
    response = ask(client, "offline")
    assert response.status_code == 503 and "internal-host" not in response.text


def test_committed_openapi_is_current():
    spec = Path(__file__).parent.parent / "openapi" / "imodar.json"
    assert json.loads(spec.read_text()) == app.openapi(), "Run scripts/export_openapi.py"
