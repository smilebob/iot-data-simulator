"""
User and Authentication Domain Models.

Defines schemas for role-based access control (RBAC), user authentication,
credential complexity validation, password modification, and public profile views.
"""

import re
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class UserRole(str, Enum):
    """Role-based access control (RBAC) authorization tiers.

    Attributes:
        ADMIN: Full control over simulation, devices, broker, scenarios, and user accounts.
        OPERATOR: Can manage devices, edit variables, trigger chaos injection, and start/stop engine.
        VIEWER: Read-only access for monitoring live telemetry and dashboards.
    """
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class User(BaseModel):
    """Internal user representation including hashed authentication credentials.

    Attributes:
        username: Unique login identifier (lowercase alphanumeric with dots/hyphens).
        full_name: Full display name or organization role.
        role: Assigned RBAC privilege role.
        password_hash: Salted Scrypt cryptographic hash ($scrypt$N$r$p$salt$key).
        created_at: ISO-8601 timestamp of account creation.
        last_login: ISO-8601 timestamp of the most recent authentication.
        is_active: Whether account is enabled and allowed to log in.
        must_change_password: Force credential change on next login (CIS benchmark).
    """
    username: str = Field(..., min_length=3, max_length=50, description="Unique username identifier")
    full_name: str = Field(..., max_length=100, description="Full display name")
    role: UserRole = Field(default=UserRole.OPERATOR, description="Assigned RBAC role")
    password_hash: str = Field(..., description="Scrypt cryptographic password hash")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_login: Optional[str] = None
    is_active: bool = Field(default=True, description="Account active status")
    must_change_password: bool = Field(default=False, description="Require password change on next login")


class UserPublic(BaseModel):
    """Public sanitized user representation safe for API serialization (no secrets or hashes).

    Attributes:
        username: Unique username identifier.
        full_name: Full display name.
        role: Assigned RBAC role.
        created_at: Account creation timestamp.
        last_login: Optional last authentication timestamp.
        is_active: Account active status.
        must_change_password: Password change requirement status.
    """
    username: str
    full_name: str
    role: UserRole
    created_at: str
    last_login: Optional[str] = None
    is_active: bool
    must_change_password: bool = False


class UserCreate(BaseModel):
    """Input payload schema for administrator creating a new user account.

    Attributes:
        username: Proposed unique identifier.
        full_name: Display name.
        role: Initial RBAC role.
        password: Raw password validated against CIS complexity rules.
    """
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=2, max_length=100)
    role: UserRole = Field(default=UserRole.OPERATOR)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Sanitizes and enforces alphanumeric rules on username."""
        v = v.strip().lower()
        if not re.match(r"^[a-z0-9_\-\.]+$", v):
            raise ValueError("Username can only contain lowercase letters, numbers, hyphens, dots, and underscores.")
        return v

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """Enforces CIS password complexity rules (uppercase, lowercase, number, minimum 8 characters)."""
        if len(v) < 8:
            raise ValueError("Password must contain at least 8 characters.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number.")
        return v


class UserPasswordChange(BaseModel):
    """Self-service password modification payload for currently authenticated user.

    Attributes:
        current_password: Existing plain-text password for identity confirmation.
        new_password: New proposed password meeting complexity requirements.
    """
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validates new credential complexity."""
        if len(v) < 8:
            raise ValueError("New password must contain at least 8 characters.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("New password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("New password must contain at least one lowercase letter.")
        if not re.search(r"[0-9]", v):
            raise ValueError("New password must contain at least one number.")
        return v


class UserPasswordReset(BaseModel):
    """Administrator-initiated password reset payload for a target user account.

    Attributes:
        new_password: Temporary or reset password for the account.
    """
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_reset_password(cls, v: str) -> str:
        """Enforces minimum length on reset password."""
        if len(v) < 8:
            raise ValueError("Password must contain at least 8 characters.")
        return v


class LoginRequest(BaseModel):
    """Authentication request credentials schema.

    Attributes:
        username: Account identifier.
        password: Plain-text password for Scrypt verification.
    """
    username: str
    password: str


class LoginResponse(BaseModel):
    """Successful authentication response payload.

    Attributes:
        status: Operation status string ('success').
        user: Public profile information of the authenticated user.
        token: Signed JWT access token for session authorization.
    """
    status: str = "success"
    user: UserPublic
    token: str
