import pytest

from imodar.guard import validate


def test_guard_accepts_and_engine_runs_select(warehouse):
    report = validate("SELECT count(*) AS n FROM omop.person", warehouse.schema, set())
    assert report.ok, report.errors
    assert warehouse.execute(report.sql).df.n.iloc[0] == 2


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT 1; DROP TABLE omop.person",
        "DELETE FROM omop.person",
        "SELECT * FROM read_csv('secret.csv')",
        "SELECT getenv('SECRET')",
        "SELECT * FROM passwords",
        "SELECT invented FROM omop.person",
        "SELECT * FROM omop.person WHERE person_id = 2999999999",
    ],
)
def test_guard_rejects(warehouse, sql):
    assert not validate(sql, warehouse.schema, set()).ok


def test_engine_is_read_only(warehouse):
    assert warehouse.execute("DELETE FROM omop.person").error


def test_engine_limits_rows_but_reports_total(warehouse):
    result = warehouse.execute("SELECT * FROM omop.person", max_rows=1)
    assert (result.returned_rows, result.row_count, result.truncated) == (1, 2, True)


def test_engine_times_out(warehouse):
    result = warehouse.execute("SELECT sum(a.range * b.range) FROM range(1000000) a, range(1000000) b", timeout_s=0.05)
    assert "timeout" in result.error
