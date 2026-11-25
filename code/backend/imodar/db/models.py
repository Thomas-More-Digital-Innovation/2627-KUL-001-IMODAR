"""Application data only; study data stays in the read-only DuckDB warehouse."""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, MetaData, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    # Stable names let Alembic alter or drop constraints later.
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


class Role(enum.StrEnum):
    INTERN = "intern"
    RESEARCHER = "researcher"
    ADMIN = "admin"


class UserStatus(enum.StrEnum):
    INVITED = "invited"
    ACTIVE = "active"
    SUSPENDED = "suspended"


def _values(members: type[enum.StrEnum]) -> list[str]:
    return [member.value for member in members]


class User(Base):
    """A workspace account."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320))
    full_name: Mapped[str] = mapped_column(String(200))
    role: Mapped[Role] = mapped_column(
        Enum(Role, name="role", native_enum=False, length=20, create_constraint=True, values_callable=_values)
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="status", native_enum=False, length=20, create_constraint=True, values_callable=_values),
        default=UserStatus.INVITED,
    )
    # Nullable so accounts that only use SSO can be added later.
    password_hash: Mapped[str | None] = mapped_column(String(255))
    totp_secret: Mapped[str | None] = mapped_column(String(255))
    totp_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    totp_last_step: Mapped[int | None]
    failed_attempts: Mapped[int] = mapped_column(default=0, server_default="0")
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SessionStage(enum.StrEnum):
    PENDING = "pending"
    FULL = "full"


class UserSession(Base):
    """A signed-in device; the token itself is only known to the browser."""

    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    stage: Mapped[SessionStage] = mapped_column(
        Enum(SessionStage, name="stage", native_enum=False, length=20, create_constraint=True, values_callable=_values)
    )
    remember: Mapped[bool]
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RecoveryCode(Base):
    """An unused 2FA recovery code; rows are deleted on use."""

    __tablename__ = "recovery_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    code_hash: Mapped[str] = mapped_column(String(64))


Index("uq_users_email_lower", func.lower(User.email), unique=True)
