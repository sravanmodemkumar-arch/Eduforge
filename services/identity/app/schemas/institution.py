import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.institution import PortalType


class InstitutionCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    code: str = Field(..., min_length=2, max_length=50)
    portal_type: PortalType
    subscription_plan: str | None = None
    settings: dict | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(None, max_length=20)
    address: str | None = Field(None, max_length=500)
    city: str | None = Field(None, max_length=100)
    state: str | None = Field(None, max_length=100)
    pincode: str | None = Field(None, max_length=10)


class InstitutionUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)
    portal_type: PortalType | None = None
    subscription_plan: str | None = None
    is_active: bool | None = None
    settings: dict | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(None, max_length=20)
    address: str | None = Field(None, max_length=500)
    city: str | None = Field(None, max_length=100)
    state: str | None = Field(None, max_length=100)
    pincode: str | None = Field(None, max_length=10)


class InstitutionResponse(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    portal_type: PortalType
    subscription_plan: str | None = None
    is_active: bool
    settings: dict | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
