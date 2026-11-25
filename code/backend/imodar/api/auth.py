"""Authentication endpoints and dependencies."""

from dataclasses import dataclass
from typing import Annotated

import segno
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from .. import config
from ..auth import service
from ..db.models import Role, SessionStage, User, UserSession
from ..db.session import get_session
from .contracts import (
    ChangePasswordRequest,
    CodeRequest,
    CurrentUser,
    EnrolmentResponse,
    LoginRequest,
    LoginResponse,
    RecoveryCodesResponse,
)

COOKIE = "imodar_session"
router = APIRouter(prefix="/api/auth", tags=["auth"], responses={401: {"description": "Not authenticated"}})
Db = Annotated[Session, Depends(get_session)]


@dataclass(frozen=True)
class Principal:
    user_id: int
    session_id: int
    email: str
    full_name: str
    role: Role


def _unauthorised(detail: str) -> HTTPException:
    return HTTPException(401, detail)


def require_user(request: Request, db: Db) -> Principal:
    """Require a session that completed the second factor."""
    try:
        session, user = service.find_session(db, request.cookies.get(COOKIE), SessionStage.FULL)
    except service.AuthError:
        raise _unauthorised("Sign in to continue.") from None
    principal = Principal(user.id, session.id, user.email, user.full_name, user.role)
    # Returns the connection to the pool; an analysis can run for minutes.
    db.rollback()
    return principal


def require_pending(request: Request, db: Db) -> tuple[UserSession, User]:
    try:
        return service.find_session(db, request.cookies.get(COOKIE), SessionStage.PENDING)
    except service.AuthError:
        raise _unauthorised("Your sign-in expired. Start again.") from None


CurrentPrincipal = Annotated[Principal, Depends(require_user)]
Pending = Annotated[tuple[UserSession, User], Depends(require_pending)]


def _set_cookie(response: Response, token: str, max_age: int | None) -> None:
    response.set_cookie(
        COOKIE, token, max_age=max_age, httponly=True, secure=config.COOKIE_SECURE, samesite="strict", path="/"
    )


def _max_age(remember: bool) -> int | None:
    return int(service.REMEMBER_TTL.total_seconds()) if remember else None


@router.post("/login")
def login(body: LoginRequest, request: Request, response: Response, db: Db) -> LoginResponse:
    """Check the password. The second factor is still required afterwards."""
    try:
        token, user = service.login(db, body.email, body.password, body.remember)
    except service.AuthError:
        raise _unauthorised("Incorrect details, or the account is temporarily locked.") from None
    enrolled = user.totp_confirmed_at is not None
    service.logout(db, request.cookies.get(COOKIE))
    _set_cookie(response, token, None)
    return LoginResponse(next="verify" if enrolled else "enrol")


@router.post("/2fa/enrol")
def enrol(pending: Pending, response: Response, db: Db) -> EnrolmentResponse:
    """Start 2FA enrolment; replaces any unconfirmed secret."""
    try:
        secret, uri = service.begin_enrolment(db, pending[1])
    except service.AuthError:
        raise HTTPException(409, "Two-factor authentication is already set up.") from None
    response.headers["Cache-Control"] = "no-store"
    return EnrolmentResponse(secret=secret, qr_code=segno.make(uri).svg_data_uri(scale=5))


@router.post("/2fa/confirm")
def confirm(body: CodeRequest, pending: Pending, response: Response, db: Db) -> RecoveryCodesResponse:
    """Finish enrolment, sign in and show the recovery codes once."""
    remember = pending[0].remember
    try:
        token, codes = service.confirm_enrolment(db, *pending, body.code)
    except service.AuthError:
        raise _unauthorised("The code is incorrect, or the account is temporarily locked.") from None
    _set_cookie(response, token, _max_age(remember))
    response.headers["Cache-Control"] = "no-store"
    return RecoveryCodesResponse(recovery_codes=codes)


@router.post("/2fa/verify", status_code=204)
def verify(body: CodeRequest, pending: Pending, response: Response, db: Db) -> None:
    """Complete sign-in with an authenticator or recovery code."""
    remember = pending[0].remember
    try:
        token = service.verify_second_factor(db, *pending, body.code)
    except service.AuthError:
        raise _unauthorised("The code is incorrect, or the account is temporarily locked.") from None
    _set_cookie(response, token, _max_age(remember))


@router.get("/me")
def me(principal: CurrentPrincipal) -> CurrentUser:
    """Return the signed-in user."""
    return CurrentUser(email=principal.email, full_name=principal.full_name, role=principal.role)


@router.post("/password", status_code=204)
def change_password(body: ChangePasswordRequest, principal: CurrentPrincipal, db: Db) -> None:
    """Change the password and sign out other devices."""
    try:
        service.change_password(db, principal.session_id, principal.user_id, body.current_password, body.new_password)
    except service.AuthError:
        raise HTTPException(400, "The current password is incorrect, or the account is temporarily locked.") from None


@router.post("/sessions/revoke-others", status_code=204)
def revoke_others(principal: CurrentPrincipal, db: Db) -> None:
    """Sign out every other device."""
    service.revoke_others(db, principal.session_id, principal.user_id)


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: Db) -> None:
    """End the current session."""
    service.logout(db, request.cookies.get(COOKIE))
    response.delete_cookie(COOKIE, path="/", httponly=True, secure=config.COOKIE_SECURE, samesite="strict")
