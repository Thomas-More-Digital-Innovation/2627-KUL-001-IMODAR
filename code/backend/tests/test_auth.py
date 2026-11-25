from datetime import UTC, datetime, timedelta

import pyotp
import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from imodar import config
from imodar.api.main import app
from imodar.auth import service
from imodar.db.models import RecoveryCode, User, UserSession, UserStatus
from imodar.db.session import get_session

EMAIL, PASSWORD = "admin@example.com", "synthetic-test-password"


@pytest.fixture
def client(session, monkeypatch):
    monkeypatch.setattr(config, "APP_SECRET_KEY", Fernet.generate_key().decode())
    service.ensure_admin(session, EMAIL, "Admin", PASSWORD)
    app.dependency_overrides[get_session] = lambda: session
    yield TestClient(app, base_url="https://testserver")
    app.dependency_overrides.clear()


def post(client, path, **body):
    return client.post(f"/api/auth/{path}", json=body)


def login(client, password=PASSWORD, **extra):
    return post(client, "login", email=EMAIL, password=password, **extra)


def enrol(client, **extra):
    assert login(client, **extra).json() == {"next": "enrol"}
    secret = client.post("/api/auth/2fa/enrol").json()["secret"]
    response = post(client, "2fa/confirm", code=pyotp.TOTP(secret).now())
    assert response.status_code == 200
    return secret, response.json()["recovery_codes"]


def me(client):
    return client.get("/api/auth/me")


@pytest.mark.parametrize("method,path", [("GET", "/api/studies"), ("POST", "/api/analyses"), ("GET", "/api/auth/me")])
def test_anonymous_is_rejected(client, method, path):
    assert client.request(method, path, json={"question": "x"}).status_code == 401


def test_password_alone_grants_nothing(client):
    login(client)
    assert me(client).status_code == 401
    assert client.get("/api/studies").status_code == 401


def test_enrolment_signs_in_and_stores_no_plaintext(client, session):
    secret, codes = enrol(client)
    assert me(client).json() == {"email": EMAIL, "full_name": "Admin", "role": "admin"}
    user = session.scalars(select(User)).one()
    assert secret not in user.totp_secret and PASSWORD not in user.password_hash
    stored = session.scalars(select(RecoveryCode.code_hash)).all()
    assert len(stored) == 10 and not set(stored) & set(codes)
    assert client.cookies["imodar_session"] not in session.scalars(select(UserSession.token_hash)).all()


def test_cookie_flags_and_token_rotation(client):
    first = login(client, remember=True)
    header = first.headers["set-cookie"].lower()
    assert all(flag in header for flag in ("httponly", "secure", "samesite=strict"))
    pending = client.cookies["imodar_session"]
    enrol(client)
    assert client.cookies["imodar_session"] != pending


def test_enrolled_user_cannot_re_enrol_with_password_only(client):
    enrol(client)
    assert login(client).json() == {"next": "verify"}
    assert client.post("/api/auth/2fa/enrol").status_code == 409
    assert me(client).status_code == 401


def test_code_cannot_be_replayed(client, session):
    secret, _ = enrol(client)
    login(client)
    user = session.scalars(select(User)).one()
    used = pyotp.TOTP(secret).generate_otp(user.totp_last_step)
    assert post(client, "2fa/verify", code=used).status_code == 401
    fresh = pyotp.TOTP(secret).generate_otp(user.totp_last_step + 1)
    assert post(client, "2fa/verify", code=fresh).status_code == 204
    assert me(client).status_code == 200


def test_recovery_code_works_once(client):
    _, codes = enrol(client)
    login(client)
    assert post(client, "2fa/verify", code=codes[0]).status_code == 204
    login(client)
    assert post(client, "2fa/verify", code=codes[0]).status_code == 401


def test_failures_lock_even_with_correct_password(client, session):
    for _ in range(5):
        assert login(client, "wrong").status_code == 401
    assert login(client).status_code == 401
    session.execute(update(User).values(locked_until=datetime.now(UTC) - timedelta(seconds=1)))
    session.commit()
    assert login(client).status_code == 200


def test_relogging_in_does_not_reset_code_guesses(client):
    enrol(client)
    for _ in range(5):
        login(client)
        post(client, "2fa/verify", code="ffffff")
    assert login(client).status_code == 401


def test_unknown_email_and_wrong_password_look_the_same(client):
    unknown = post(client, "login", email="nobody@example.com", password="x")
    assert (unknown.status_code, unknown.json()) == (401, login(client, "wrong").json())


def test_suspension_and_expiry_end_access(client, session):
    enrol(client)
    session.execute(update(User).values(status=UserStatus.SUSPENDED))
    session.commit()
    assert me(client).status_code == 401
    session.execute(update(User).values(status=UserStatus.ACTIVE))
    session.execute(update(UserSession).values(expires_at=datetime.now(UTC) - timedelta(seconds=1)))
    session.commit()
    assert me(client).status_code == 401


def test_password_change_signs_out_other_devices(client):
    _, codes = enrol(client)
    other = TestClient(app, base_url="https://testserver")
    login(other)
    post(other, "2fa/verify", code=codes[0])
    assert me(other).status_code == 200
    assert post(client, "password", current_password="wrong", new_password="x" * 12).status_code == 400
    assert post(client, "password", current_password=PASSWORD, new_password="short").status_code == 422
    assert post(client, "password", current_password=PASSWORD, new_password="another-test-password").status_code == 204
    assert (me(client).status_code, me(other).status_code) == (200, 401)
    assert login(other).status_code == 401


def test_logout_invalidates_the_token(client):
    enrol(client)
    token = client.cookies["imodar_session"]
    client.post("/api/auth/logout")
    client.cookies.set("imodar_session", token)
    assert me(client).status_code == 401


def test_seed_never_overwrites(client, session):
    before = session.scalars(select(User.password_hash)).one()
    assert service.ensure_admin(session, EMAIL.upper(), "Other", "a-different-password") is False
    assert session.scalars(select(User.password_hash)).one() == before
    with pytest.raises(ValueError):
        service.ensure_admin(session, "b@example.com", "B", "short")
