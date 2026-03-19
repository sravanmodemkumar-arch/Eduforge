import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    phone: str = Field(..., min_length=10, max_length=15)
    email: EmailStr | None = None
    full_name: str | None = None
    role: UserRole = UserRole.STUDENT
    institution_id: uuid.UUID | None = None
    metadata: dict | None = None


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    phone: str | None = Field(None, min_length=10, max_length=15)
    role: UserRole | None = None
    institution_id: uuid.UUID | None = None
    is_active: bool | None = None
    metadata: dict | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    phone: str
    email: str | None = None
    full_name: str | None = None
    role: UserRole
    institution_id: uuid.UUID | None = None
    is_active: bool
    metadata: dict | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    page_size: int
    pages: int
