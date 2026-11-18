import uuid
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.api.deps import get_current_user, get_db_session
from backend.app.core.rate_limit import rate_limit_auth
from backend.app.core.security import create_access_token, get_password_hash, verify_password
from backend.app.models.student import Student
from backend.app.models.user import User

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    role: str = Field(default="STUDENT")
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    department: str = Field(default="Computer Science")
    bio: Optional[str] = None
    statement_of_purpose: Optional[str] = None


class UserProfileResponse(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    is_active: bool
    student_id: Optional[uuid.UUID] = None
    faculty_id: Optional[uuid.UUID] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    department: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfileResponse


def _build_user_profile(user: User) -> UserProfileResponse:
    first_name = None
    last_name = None
    student_id = None
    faculty_id = None
    department = None

    if user.student_profile:
        first_name = user.student_profile.first_name
        last_name = user.student_profile.last_name
        student_id = user.student_profile.id
        department = user.student_profile.department
    elif user.faculty_profile:
        first_name = user.faculty_profile.first_name
        last_name = user.faculty_profile.last_name
        faculty_id = user.faculty_profile.id
        department = user.faculty_profile.department

    full_name = f"{first_name} {last_name}".strip() if (first_name or last_name) else user.email.split("@")[0]

    return UserProfileResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        student_id=student_id,
        faculty_id=faculty_id,
        first_name=first_name,
        last_name=last_name,
        full_name=full_name,
        department=department,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and return JWT bearer token",
    dependencies=[Depends(rate_limit_auth)],
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    stmt = (
        select(User)
        .where(User.email == request.email.lower().strip())
        .options(
            selectinload(User.student_profile),
            selectinload(User.faculty_profile),
        )
    )
    user = (await db.execute(stmt)).scalars().first()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    user_profile = _build_user_profile(user)
    token = create_access_token(
        subject=user.id,
        role=user.role,
        extra_claims={
            "email": user.email,
            "student_id": str(user_profile.student_id) if user_profile.student_id else None,
            "faculty_id": str(user_profile.faculty_id) if user_profile.faculty_id else None,
        },
    )

    return TokenResponse(access_token=token, user=user_profile)


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new student account",
    dependencies=[Depends(rate_limit_auth)],
)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    # Check if email exists
    existing = (
        await db.execute(select(User).where(User.email == request.email.lower().strip()))
    ).scalars().first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists",
        )

    role_upper = request.role.upper()
    if role_upper != "STUDENT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Public registration is limited to STUDENT accounts.",
        )

    user = User(
        id=uuid.uuid4(),
        email=request.email.lower().strip(),
        hashed_password=get_password_hash(request.password),
        role=role_upper,
        is_active=True,
    )
    db.add(user)
    await db.flush()

    if role_upper == "STUDENT":
        student = Student(
            id=uuid.uuid4(),
            user_id=user.id,
            first_name=request.first_name,
            last_name=request.last_name,
            department=request.department,
            statement_of_purpose=request.statement_of_purpose or f"Interested in {request.department} research.",
            bio=request.bio or "",
        )
        db.add(student)
    await db.commit()

    # Re-fetch with relationships
    stmt = (
        select(User)
        .where(User.id == user.id)
        .options(
            selectinload(User.student_profile),
            selectinload(User.faculty_profile),
        )
    )
    refetched = (await db.execute(stmt)).scalars().first()
    user_profile = _build_user_profile(refetched)

    token = create_access_token(
        subject=user.id,
        role=user.role,
        extra_claims={
            "email": user.email,
            "student_id": str(user_profile.student_id) if user_profile.student_id else None,
            "faculty_id": str(user_profile.faculty_id) if user_profile.faculty_id else None,
        },
    )

    return TokenResponse(access_token=token, user=user_profile)


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get details of currently authenticated user",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserProfileResponse:
    return _build_user_profile(current_user)
