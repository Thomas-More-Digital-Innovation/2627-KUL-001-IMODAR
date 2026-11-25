from alembic import context

from imodar.db.models import Base
from imodar.db.session import get_engine

if context.is_offline_mode():
    raise SystemExit("Offline migrations are not supported.")

with get_engine().connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()
