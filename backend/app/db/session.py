# app/db/session.py
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from core.config import settings
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

raw_url = settings.DATABASE_URL

# Convert postgres:// or postgresql:// to asyncpg
if raw_url.startswith("postgresql://"):
    raw_url = raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif raw_url.startswith("postgres://"):
    raw_url = raw_url.replace("postgres://", "postgresql+asyncpg://", 1)

# ---- STRIP sslmode from query params ----
parsed = urlparse(raw_url)
query = parse_qs(parsed.query)

query.pop("sslmode", None)          # ❗ asyncpg does not support this
query.pop("channel_binding", None)  # ❗ also not supported by asyncpg

clean_query = urlencode(query, doseq=True)

DATABASE_URL = urlunparse(parsed._replace(query=clean_query))

# SSL only when explicitly requested (managed cloud DBs).
# Local / docker-compose postgres has no SSL -> ssl=False (or unset).
# Set DB_SSL=true (or sslmode=require in DATABASE_URL) to enable.
_want_ssl = os.getenv("DB_SSL", "").lower() in ("1", "true", "yes", "require")
if "sslmode=require" in settings.DATABASE_URL:
    _want_ssl = True

connect_args = {"ssl": True} if _want_ssl else {}

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args=connect_args,
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
