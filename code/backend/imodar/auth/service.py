"""Sign-in flow: password, then a mandatory second factor, then a full session."""

from datetime import UTC, datetime, timedelta

import pyotp
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ..db.models import RecoveryCode, Role, SessionStage, User, UserSession, UserStatus
from . import security

PENDING_TTL = timedelta(minutes=10)
SESSION_TTL = timedelta(hours=12)
REMEMBER_TTL = timedelta(days=30)
MAX_FAILURES = 5
LOCK_TIME = timedelta(minutes=15)


class AuthError(Exception):
    """Deliberately carries no reason, so callers cannot leak one."""


def _locked(user: User) -> bool:
    return user.locked_until is not None and user.locked_until > datetime.now(UTC)


def _record_failure(db: Session, user: User) -> None:
    user.failed_attempts += 1
    if user.failed_attempts >= MAX_FAILURES:
        user.locked_until = datetime.now(UTC) + LOCK_TIME
        user.failed_attempts = 0
    db.commit()


def _lock_row(db: Session, user_id: int) -> User:
    # Serialises attempts, so parallel guesses cannot bypass the counter or reuse a code.
    return db.scalars(
        select(User).where(User.id == user_id).with_for_update().execution_options(populate_existing=True)
    ).one()


def _create_session(db: Session, user_id: int, stage: SessionStage, remember: bool, ttl: timedelta) -> str:
    token = security.new_token()
    db.add(
        UserSession(
            user_id=user_id,
            token_hash=security.digest(token),
            stage=stage,
            remember=remember,
            expires_at=datetime.now(UTC) + ttl,
        )
    )
    return token


def login(db: Session, email: str, password: str, remember: bool) -> tuple[str, User]:
    """Check the password and return a pending session token; it grants no data access."""
    user = db.scalars(select(User).where(func.lower(User.email) == email.strip().lower()).with_for_update()).first()
    valid = security.verify_password(user.password_hash if user else None, password)
    if user is None or user.status is not UserStatus.ACTIVE or _locked(user):
        raise AuthError
    if not valid:
        _record_failure(db, user)
        raise AuthError
    # Failures are reset only after the second factor, or a known password would allow unlimited code guesses.
    db.execute(delete(UserSession).where(UserSession.user_id == user.id, UserSession.expires_at < func.now()))
    token = _create_session(db, user.id, SessionStage.PENDING, remember, PENDING_TTL)
    db.commit()
    return token, user


def find_session(db: Session, token: str | None, stage: SessionStage) -> tuple[UserSession, User]:
    if not token:
        raise AuthError
    row = db.execute(
        select(UserSession, User)
        .join(User, User.id == UserSession.user_id)
        .where(
            UserSession.token_hash == security.digest(token),
            UserSession.stage == stage,
            UserSession.expires_at > func.now(),
            User.status == UserStatus.ACTIVE,
        )
    ).first()
    if row is None:
        raise AuthError
    return row[0], row[1]


def _promote(db: Session, pending: UserSession, user: User) -> str:
    user.failed_attempts = 0
    user.locked_until = None
    ttl = REMEMBER_TTL if pending.remember else SESSION_TTL
    token = _create_session(db, user.id, SessionStage.FULL, pending.remember, ttl)
    db.delete(pending)
    db.commit()
    return token


def begin_enrolment(db: Session, user: User) -> tuple[str, str]:
    """Return a new TOTP secret and its provisioning URI."""
    user = _lock_row(db, user.id)
    if user.totp_confirmed_at is not None:
        raise AuthError
    secret = pyotp.random_base32()
    user.totp_secret = security.cipher().encrypt(secret.encode()).decode()
    db.commit()
    return secret, pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="IMODAR")


def _check_totp(user: User, code: str) -> bool:
    if user.totp_secret is None:
        return False
    secret = security.cipher().decrypt(user.totp_secret.encode()).decode()
    step = security.matching_step(secret, code, user.totp_last_step)
    if step is None:
        return False
    user.totp_last_step = step
    return True


def _normalise(code: str) -> str:
    return code.replace(" ", "").replace("-", "").lower()


def confirm_enrolment(db: Session, pending: UserSession, user: User, code: str) -> tuple[str, list[str]]:
    """Activate 2FA and return the full session token with one-time recovery codes."""
    user = _lock_row(db, user.id)
    if user.totp_confirmed_at is not None or _locked(user):
        raise AuthError
    if not _check_totp(user, _normalise(code)):
        _record_failure(db, user)
        raise AuthError
    user.totp_confirmed_at = datetime.now(UTC)
    codes = security.new_recovery_codes()
    db.add_all(RecoveryCode(user_id=user.id, code_hash=security.digest(item)) for item in codes)
    return _promote(db, pending, user), codes


def _use_recovery_code(db: Session, user: User, code: str) -> bool:
    result = db.execute(
        delete(RecoveryCode).where(RecoveryCode.user_id == user.id, RecoveryCode.code_hash == security.digest(code))
    )
    return result.rowcount == 1


def verify_second_factor(db: Session, pending: UserSession, user: User, code: str) -> str:
    user = _lock_row(db, user.id)
    code = _normalise(code)
    if user.totp_confirmed_at is None or _locked(user):
        raise AuthError
    if not (_check_totp(user, code) or _use_recovery_code(db, user, code)):
        _record_failure(db, user)
        raise AuthError
    return _promote(db, pending, user)


def change_password(db: Session, session_id: int, user_id: int, current: str, new: str) -> None:
    """Change the password and sign out every other device."""
    user = _lock_row(db, user_id)
    if _locked(user):
        raise AuthError
    if not security.verify_password(user.password_hash, current):
        _record_failure(db, user)
        raise AuthError
    user.password_hash = security.hash_password(new)
    user.failed_attempts = 0
    revoke_others(db, session_id, user_id)


def revoke_others(db: Session, session_id: int, user_id: int) -> None:
    db.execute(delete(UserSession).where(UserSession.user_id == user_id, UserSession.id != session_id))
    db.commit()


def logout(db: Session, token: str | None) -> None:
    if token:
        db.execute(delete(UserSession).where(UserSession.token_hash == security.digest(token)))
        db.commit()


def ensure_admin(db: Session, email: str, name: str, password: str) -> bool:
    """Create the first admin; an existing account is never modified."""
    email = email.strip().lower()
    if "@" not in email or len(password) < 12:
        raise ValueError("Set ADMIN_EMAIL, and an ADMIN_PASSWORD of at least 12 characters.")
    if db.scalar(select(User.id).where(func.lower(User.email) == email)) is not None:
        return False
    db.add(
        User(
            email=email,
            full_name=name.strip() or "Administrator",
            role=Role.ADMIN,
            status=UserStatus.ACTIVE,
            password_hash=security.hash_password(password),
        )
    )
    db.commit()
    return True
