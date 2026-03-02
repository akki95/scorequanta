import os
import ssl as ssl_module
from urllib.parse import urlparse, urlunparse, quote_plus
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

raw_url = os.environ.get("SUPABASE_DATABASE_URL", os.environ.get("DATABASE_URL", ""))

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

ssl_context = ssl_module.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl_module.CERT_NONE

engine = create_async_engine(DATABASE_URL, echo=False, pool_size=5, max_overflow=10,
                             connect_args={"ssl": ssl_context})
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
