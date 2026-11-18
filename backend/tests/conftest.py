import asyncio
import uuid
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from backend.app.api.deps import get_db_session
from backend.app.core.security import create_access_token
from backend.app.core.rate_limit import auth_limiter, general_limiter
from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.main import app
from backend.app.models.user import User

# In-memory SQLite engine for rapid, isolated testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)

test_async_session_maker = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Create a fresh database for each test function."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with test_async_session_maker() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    """FastAPI test client with database dependency override."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_db_session] = override_get_db

    auth_limiter.reset()
    general_limiter.reset()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def sample_student_user(db_session: AsyncSession) -> User:
    """Fixture creating a student user in the database."""
    user = User(
        id=uuid.uuid4(),
        email=f"student_{uuid.uuid4().hex[:8]}@university.edu",
        hashed_password="mock_hashed_password_123",
        role="STUDENT",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def sample_faculty_user(db_session: AsyncSession) -> User:
    """Fixture creating a faculty user in the database."""
    user = User(
        id=uuid.uuid4(),
        email=f"prof_{uuid.uuid4().hex[:8]}@university.edu",
        hashed_password="mock_hashed_password_456",
        role="FACULTY",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_auth_headers(db_session: AsyncSession) -> dict[str, str]:
    """Create an isolated active admin and return its authenticated request headers."""
    user = User(
        id=uuid.uuid4(),
        email=f"admin_{uuid.uuid4().hex[:8]}@university.edu",
        hashed_password="unused_test_hash",
        role="ADMIN",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    token = create_access_token(subject=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}
