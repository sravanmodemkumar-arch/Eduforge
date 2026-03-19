from pydantic import BaseModel, Field


class OTPRequestSchema(BaseModel):
    phone: str = Field(
        ...,
        min_length=10,
        max_length=15,
        description="Phone number with country code, e.g. +919876543210",
        examples=["+919876543210"],
    )


class OTPVerifySchema(BaseModel):
    phone: str = Field(
        ...,
        min_length=10,
        max_length=15,
        description="Phone number with country code",
        examples=["+919876543210"],
    )
    otp: str = Field(
        ...,
        min_length=4,
        max_length=6,
        description="OTP received via WhatsApp/SMS",
        examples=["123456"],
    )


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token expiry in seconds")


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token to exchange for a new access token")


class MessageResponse(BaseModel):
    message: str
