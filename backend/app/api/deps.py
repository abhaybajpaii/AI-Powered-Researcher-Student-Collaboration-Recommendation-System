import uuid
from typing import AsyncGenerator, List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.core.security import decode_access_token
from backend.app.db.session import get_db
from backend.app.models.user import User

security_scheme = HTTPBearer(auto_error=False)


async def get_db_session(
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async database session."""
    yield db


async def get_current_user_optional(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> Optional[User]:
    """Retrieves current user if authorization header is present and valid."""
    if not auth or not auth.credentials:
        return None

    payload = decode_access_token(auth.credentials)
    if not payload or "sub" not in payload:
        return None

    try:
        user_id = uuid.UUID(payload["sub"])
    except (ValueError, TypeError):
        return None

    stmt = (
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.student_profile),
            selectinload(User.faculty_profile),
        )
    )
    user = (await db.execute(stmt)).scalars().first()
    return user


async def get_current_user(
    user: Optional[User] = Depends(get_current_user_optional),
) -> User:
    """Enforces authentication: raises 401 if token is missing or invalid."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials or token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
    return user


def require_role(allowed_roles: List[str]):
    """Returns a dependency function checking if current user has an allowed role."""

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted for role '{current_user.role}'. Required: {allowed_roles}",
            )
        return current_user

    return role_checker
