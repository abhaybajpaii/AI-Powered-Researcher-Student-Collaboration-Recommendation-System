from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    email: str = Field(
        ...,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        max_length=255,
        description="Standard email format",
    )
    role: str = Field(default="STUDENT", description="STUDENT, FACULTY, or ADMIN")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserResponse(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
