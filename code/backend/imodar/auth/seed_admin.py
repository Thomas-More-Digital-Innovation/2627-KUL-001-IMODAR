"""Create the first admin from the environment: uv run python -m imodar.auth.seed_admin"""

import os

from sqlalchemy.orm import Session

from .. import config  # noqa: F401 - loads .env
from ..db.session import get_engine
from .service import ensure_admin

if __name__ == "__main__":
    with Session(get_engine()) as db:
        try:
            created = ensure_admin(
                db,
                os.getenv("ADMIN_EMAIL", ""),
                os.getenv("ADMIN_NAME", ""),
                os.getenv("ADMIN_PASSWORD", ""),
            )
        except ValueError as error:
            raise SystemExit(str(error)) from None
    print("Admin created." if created else "Admin already exists; nothing changed.")
