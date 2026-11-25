import os
from pathlib import Path

import duckdb
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, delete, make_url
from sqlalchemy.orm import Session

from imodar import config
from imodar.db.models import User
from imodar.db.session import get_engine
from imodar.engine import Warehouse

URL = os.getenv("TEST_DATABASE_URL")
ALEMBIC = Config(Path(__file__).parent.parent / "alembic.ini")


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


@pytest.fixture(scope="session")
def engine():
    if not URL:
        pytest.skip("TEST_DATABASE_URL is not set")
    # Migrations are rolled all the way back, so a development database must never be the target.
    assert make_url(URL).database.endswith("_test"), "TEST_DATABASE_URL must name a *_test database"
    patch = pytest.MonkeyPatch()
    patch.setattr(config, "DATABASE_URL", URL)
    get_engine.cache_clear()
    command.upgrade(ALEMBIC, "head")
    engine = create_engine(URL)
    yield engine
    engine.dispose()
    command.downgrade(ALEMBIC, "base")
    get_engine().dispose()
    get_engine.cache_clear()
    patch.undo()


@pytest.fixture
def session(engine):
    with Session(engine) as session:
        yield session
        session.rollback()
        session.execute(delete(User))
        session.commit()
