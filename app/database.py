import os
import ssl as ssl_module
from urllib.parse import quote_plus
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

raw_url = os.environ.get("SUPABASE_DATABASE_URL", "")

if raw_url.startswith("postgresql"):
    from urllib.parse import urlparse, urlunparse
    parsed = urlparse(raw_url)
    password = quote_plus(parsed.password) if parsed.password else ""
    clean_netloc = f"{parsed.username}:{password}@{parsed.hostname}"
    if parsed.port:
        clean_netloc += f":{parsed.port}"
    DATABASE_URL = urlunparse((
        "postgresql+asyncpg",
        clean_netloc,
        parsed.path,
        parsed.params,
        "",
        parsed.fragment,
    ))
else:
    supabase_host = os.environ.get("SUPABASE_HOST", "")
    supabase_port = os.environ.get("SUPABASE_PORT", "6543")
    supabase_user = os.environ.get("SUPABASE_USER", "")
    supabase_db = os.environ.get("SUPABASE_DB", "postgres")
    supabase_password = quote_plus(raw_url) if raw_url else ""

    if supabase_host and supabase_user and supabase_password:
        DATABASE_URL = f"postgresql+asyncpg://{supabase_user}:{supabase_password}@{supabase_host}:{supabase_port}/{supabase_db}"
    else:
        fallback = os.environ.get("DATABASE_URL", "")
        if fallback.startswith("postgresql://"):
            fallback = fallback.replace("postgresql://", "postgresql+asyncpg://", 1)
        if "sslmode=" in fallback:
            fallback = fallback.split("?")[0]
        DATABASE_URL = fallback

ssl_context = ssl_module.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl_module.CERT_NONE

use_ssl = "pooler.supabase.com" in DATABASE_URL or "supabase" in DATABASE_URL
connect_args = {"ssl": ssl_context} if use_ssl else {}

engine = create_async_engine(DATABASE_URL, echo=False, pool_size=5, max_overflow=10,
                             connect_args=connect_args)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
