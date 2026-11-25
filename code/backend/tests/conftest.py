import duckdb
import pytest

from imodar.engine import Warehouse


@pytest.fixture
def warehouse(tmp_path):
    """A synthetic warehouse: real study data must never be needed by the test suite."""
    path = tmp_path / "test.duckdb"
    with duckdb.connect(str(path)) as connection:
        connection.execute("CREATE SCHEMA omop")
        connection.execute("CREATE SCHEMA catalog")
        connection.execute("CREATE TABLE omop.person (person_id INT, study_id VARCHAR, age_years DOUBLE)")
        connection.execute("INSERT INTO omop.person VALUES (1, 'T-1', 50), (2, 'T-1', NULL)")
        connection.execute(
            "CREATE TABLE catalog.studies "
            "(study_id VARCHAR, study_name VARCHAR, n_participants INT, modalities VARCHAR, has_data BOOLEAN)"
        )
        connection.execute(
            "INSERT INTO catalog.studies VALUES ('T-1', 'Test', 2, 'lab', true), ('T-2', 'Empty', 0, NULL, false)"
        )
    opened = Warehouse(path)
    yield opened
    opened.con.close()
