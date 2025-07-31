from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from odme_anomalies.core.config import settings

# Create the asynchronous engine using the database URL from settings
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # Enable SQL logging for debugging
)

# Create an async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,  # Explicitly declare the session class
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a new SQLAlchemy AsyncSession per request.
    This session is automatically closed after the request finishes.

    Usage:
        async def endpoint(db: AsyncSession = Depends(get_session)):
            ...
    """
    async with AsyncSessionLocal() as session:
        yield session
