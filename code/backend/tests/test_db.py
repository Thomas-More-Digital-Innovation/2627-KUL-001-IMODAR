import pytest
from alembic import command
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from imodar.db.models import Role, User, UserStatus

from .conftest import ALEMBIC


def test_models_match_migrations(engine):
    command.check(ALEMBIC)


def test_user_defaults_and_stored_values(session):
    session.add(User(email="a@example.com", full_name="A", role=Role.ADMIN))
    session.flush()
    user = session.scalars(select(User)).one()
    assert user.status is UserStatus.INVITED and user.created_at.tzinfo
    assert session.scalar(text("SELECT role FROM users")) == "admin"


def test_email_is_unique_ignoring_case(session):
    session.add(User(email="a@example.com", full_name="A", role=Role.INTERN))
    session.flush()
    session.add(User(email="A@Example.com", full_name="B", role=Role.INTERN))
    with pytest.raises(IntegrityError):
        session.flush()


def test_database_rejects_unknown_role(session):
    with pytest.raises(IntegrityError):
        session.execute(text("INSERT INTO users (email, full_name, role, status) VALUES ('x', 'x', 'root', 'active')"))
