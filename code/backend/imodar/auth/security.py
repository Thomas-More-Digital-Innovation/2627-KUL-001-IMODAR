"""Password, token and one-time-code primitives."""

import hashlib
import hmac
import secrets
import time

import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from cryptography.fernet import Fernet

from .. import config

_hasher = PasswordHasher()
# Verified for unknown accounts so response times do not reveal which emails exist.
_DUMMY_HASH = _hasher.hash(secrets.token_urlsafe())
RECOVERY_CODE_COUNT = 10


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(stored: str | None, password: str) -> bool:
    try:
        return _hasher.verify(stored or _DUMMY_HASH, password) and stored is not None
    except (VerificationError, InvalidHashError):
        return False


def new_token() -> str:
    return secrets.token_urlsafe(32)


def digest(value: str) -> str:
    """Hash for high-entropy random values only, never for passwords."""
    return hashlib.sha256(value.encode()).hexdigest()


def cipher() -> Fernet:
    if not config.APP_SECRET_KEY:
        raise RuntimeError("APP_SECRET_KEY is not set; see .env.example")
    return Fernet(config.APP_SECRET_KEY)


def matching_step(secret: str, code: str, last_step: int | None) -> int | None:
    """Return the matched time step, ignoring steps already used so codes cannot be replayed."""
    current = int(time.time()) // 30
    totp = pyotp.TOTP(secret)
    for step in (current - 1, current, current + 1):
        if (last_step is None or step > last_step) and hmac.compare_digest(
            totp.generate_otp(step).encode(), code.encode()
        ):
            return step
    return None


def new_recovery_codes() -> list[str]:
    return [secrets.token_hex(8) for _ in range(RECOVERY_CODE_COUNT)]
