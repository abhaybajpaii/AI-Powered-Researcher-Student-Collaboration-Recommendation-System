from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from backend.app.core.config import settings
from backend.app.core.logging import logger

# Configure async engine
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    connect_args=connect_args,
    pool_pre_ping=True,
)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session per request."""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def verify_database_connection() -> dict:
    """Verifies that the database is reachable and checks pgvector extension."""
    result = {
        "connected": False,
        "database_type": "unknown",
        "vector_extension": False,
        "details": None,
    }
    try:
        async with engine.connect() as conn:
            # Test simple query
            res = await conn.execute(text("SELECT 1"))
            scalar = res.scalar()
            if scalar == 1:
                result["connected"] = True

            # Determine dialect
            dialect = conn.dialect.name
            result["database_type"] = dialect

            # Check pgvector if postgresql
            if dialect == "postgresql":
                ext_res = await conn.execute(
                    text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
                )
                if ext_res.scalar():
                    result["vector_extension"] = True
            elif dialect == "sqlite":
                # For local testing without postgres
                result["vector_extension"] = True

    except Exception as exc:
        logger.error(f"Database connectivity check failed: {exc}")
        result["details"] = str(exc)

    return result
