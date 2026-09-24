# app/db/init_db.py
"""Create all tables on startup (no alembic required for local/dev)."""
from db.base import Base
from db.session import engine

# Import models so they register on Base.metadata
import models.patient  # noqa: F401
import models.study  # noqa: F401
import models.image  # noqa: F401
import models.finding  # noqa: F401
import models.decision  # noqa: F401
import models.report  # noqa: F401


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
