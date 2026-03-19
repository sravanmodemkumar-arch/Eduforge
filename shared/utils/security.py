"""Security utilities — OTP generation and hashing."""

from __future__ import annotations

import secrets

import bcrypt


def generate_otp(length: int = 6) -> str:
    """Generate a cryptographically random numeric OTP of *length* digits."""
    # secrets.randbelow is backed by os.urandom — suitable for OTPs.
    upper = 10**length
    code = secrets.randbelow(upper)
    return str(code).zfill(length)


def hash_otp(otp: str) -> str:
    """Hash an OTP string using bcrypt and return the hash as a UTF-8 string."""
    return bcrypt.hashpw(otp.encode(), bcrypt.gensalt()).decode()


def verify_otp(otp: str, hashed: str) -> bool:
    """Verify a plaintext OTP against a bcrypt hash."""
    return bcrypt.checkpw(otp.encode(), hashed.encode())
