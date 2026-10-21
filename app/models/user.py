import re
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator

class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"

class User(BaseModel):
    """Modèle interne complet d'un utilisateur avec données d'authentification."""
    username: str = Field(..., min_length=3, max_length=50, description="Identifiant unique")
    full_name: str = Field(..., max_length=100, description="Nom complet ou désignation")
    role: UserRole = Field(default=UserRole.OPERATOR, description="Rôle RBAC")
    password_hash: str = Field(..., description="Empreinte cryptographique Scrypt du mot de passe")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    last_login: Optional[str] = None
    is_active: bool = Field(default=True, description="Compte actif")
    must_change_password: bool = Field(default=False, description="Exiger le changement de mot de passe à la prochaine connexion")

class UserPublic(BaseModel):
    """Vue publique sécurisée d'un utilisateur (sans secret ni hash)."""
    username: str
    full_name: str
    role: UserRole
    created_at: str
    last_login: Optional[str] = None
    is_active: bool
    must_change_password: bool = False

class UserCreate(BaseModel):
    """Schéma de création d'un utilisateur par l'administrateur."""
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=2, max_length=100)
    role: UserRole = Field(default=UserRole.OPERATOR)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r"^[a-z0-9_\-\.]+$", v):
            raise ValueError("L'identifiant ne peut contenir que des lettres minuscules, chiffres, tirets, points et soulignés.")
        return v

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Le mot de passe doit contenir au moins une lettre majuscule.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Le mot de passe doit contenir au moins une lettre minuscule.")
        if not re.search(r"[0-9]", v):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre.")
        return v

class UserPasswordChange(BaseModel):
    """Changement de mot de passe autonome par l'utilisateur connecté."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Le nouveau mot de passe doit comporter au moins 8 caractères.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Le nouveau mot de passe doit comporter au moins une lettre majuscule.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Le nouveau mot de passe doit comporter au moins une lettre minuscule.")
        if not re.search(r"[0-9]", v):
            raise ValueError("Le nouveau mot de passe doit comporter au moins un chiffre.")
        return v

class UserPasswordReset(BaseModel):
    """Réinitialisation du mot de passe d'un utilisateur par l'administrateur."""
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_reset_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Le mot de passe doit comporter au moins 8 caractères.")
        return v

class LoginRequest(BaseModel):
    """Requête de connexion."""
    username: str
    password: str

class LoginResponse(BaseModel):
    """Réponse d'authentification réussie."""
    status: str = "success"
    user: UserPublic
    token: str
