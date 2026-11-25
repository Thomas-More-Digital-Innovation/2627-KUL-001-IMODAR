"""Engine and request-scoped sessions for the application database."""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from .. import config


@lru_cache
def get_engine() -> Engine:
    return create_engine(config.DATABASE_URL, pool_pre_ping=True, connect_args={"connect_timeout": 5})


def get_session() -> Iterator[Session]:
    """FastAPI dependency; callers commit explicitly, anything else rolls back."""
    with Session(get_engine()) as session:
        yield session
