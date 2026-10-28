"""
Authentication and Role-Based Access Control (RBAC) API Router.

This module provides FastAPI routes and dependency injection providers for:
- JWT Session Authentication: Dual support for HttpOnly cookies (browser) and Bearer header (API/CLI).
- RBAC Enforcement: `require_role([UserRole.ADMIN, ...])` route dependency guard.
- User Profile & Session Management: `/api/auth/login`, `/api/auth/logout`, `/api/auth/me`, `/api/auth/change-password`.
- Admin User Management: `/api/users` (List, Create, Delete with last-admin guard, and Password Reset).
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Request, Response, status

from app.core.security import create_jwt_token, decode_jwt_token, verify_password
from app.models.user import (
    LoginRequest,
    LoginResponse,
    User,
    UserCreate,
    UserPasswordChange,
    UserPasswordReset,
    UserPublic,
    UserRole,
)
from app.storage.user_repository import UserRepository

logger = logging.getLogger("iot_sim.auth")

auth_router = APIRouter(prefix="/api")

def get_user_repo() -> UserRepository:
    """
    FastAPI dependency returning the singleton UserRepository instance.

    Returns:
        UserRepository: Application-wide repository instance.
    """
    from app.main import user_repository
    return user_repository

def get_current_user(
    request: Request,
    access_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None),
    repo: UserRepository = Depends(get_user_repo),
) -> User:
    """
    Validates session token from HttpOnly cookie or Authorization Bearer header.

    Args:
        request: FastAPI HTTP request object.
        access_token: Optional JWT string extracted from HttpOnly cookie.
        authorization: Optional Bearer header string.
        repo: Injected UserRepository instance.

    Returns:
        User: Authenticated and active User instance.

    Raises:
        HTTPException(401): If token is missing, expired, invalid, or user is inactive.
    """
    token = None
    # 1. Inspect HttpOnly session cookie
    if access_token:
        token = access_token
    # 2. Inspect Bearer Authorization header
    elif authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session non authentifiée. Veuillez vous connecter.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_jwt_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expirée ou invalide. Veuillez vous reconnecter.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Jeton de session corrompu.",
        )

    user = repo.get_user(username)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Compte utilisateur introuvable ou désactivé.",
        )

    return user

def require_role(allowed_roles: List[UserRole]):
    """
    Factory generating RBAC authorization dependency checking user role against allowed list.

    Args:
        allowed_roles: List of UserRole enums permitted to access the endpoint.

    Returns:
        Callable: Dependency function that returns the authenticated User or raises 403 Forbidden.
    """
    def _role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            logger.warning(
                f"Accès refusé pour '{current_user.username}' (rôle: {current_user.role.value}). "
                f"Rôles autorisés : {[r.value for r in allowed_roles]}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Privilèges insuffisants ({current_user.role.value}). Action non autorisée.",
            )
        return current_user
    return _role_checker

# =========================================================================
# Authentication & User Session Endpoints
# =========================================================================

@auth_router.post("/auth/login", response_model=LoginResponse)
def login(
    req: LoginRequest,
    response: Response,
    repo: UserRepository = Depends(get_user_repo),
) -> LoginResponse:
    """
    Authenticates user credentials, verifies Scrypt hash, and sets HttpOnly cookie.

    Args:
        req: LoginRequest containing username and plaintext password.
        response: FastAPI response object for cookie setting.
        repo: Injected UserRepository instance.

    Returns:
        LoginResponse: Authentication status, public user profile, and JWT token.

    Raises:
        HTTPException(401): If credentials are invalid.
        HTTPException(403): If the account is deactivated.
    """
    user = repo.get_user(req.username)
    if not user or not verify_password(req.password, user.password_hash):
        logger.warning(f"Failed login attempt for username '{req.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiant ou mot de passe incorrect.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce compte utilisateur est désactivé.",
        )

    # Issue secure JWT token (valid for 8 hours = 28800s)
    token = create_jwt_token({
        "sub": user.username,
        "role": user.role.value,
        "name": user.full_name,
    }, expires_in_seconds=28800)

    repo.update_last_login(user.username)

    # Set secure HttpOnly cookie conforming to CIS / OWASP standards
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=28800,
        path="/",
    )

    logger.info(f"Successful login for user '{user.username}' ({user.role.value})")

    user_pub = UserPublic(
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        created_at=user.created_at,
        last_login=user.last_login,
        is_active=user.is_active,
        must_change_password=user.must_change_password,
    )

    return LoginResponse(
        status="success",
        user=user_pub,
        token=token,
    )

@auth_router.post("/auth/logout")
def logout(response: Response) -> dict:
    """
    Terminates session by invalidating the HttpOnly session cookie.

    Args:
        response: FastAPI response object.

    Returns:
        dict: Logout confirmation message.
    """
    response.delete_cookie(key="access_token", path="/")
    return {"status": "logged_out", "message": "Déconnexion réussie."}

@auth_router.get("/auth/me", response_model=UserPublic)
def get_me(current_user: User = Depends(get_current_user)) -> UserPublic:
    """
    Returns public profile of currently authenticated user.

    Args:
        current_user: User resolved from active session.

    Returns:
        UserPublic: Public user profile attributes.
    """
    return UserPublic(
        username=current_user.username,
        full_name=current_user.full_name,
        role=current_user.role,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
        is_active=current_user.is_active,
        must_change_password=current_user.must_change_password,
    )

@auth_router.post("/auth/change-password")
def change_own_password(
    data: UserPasswordChange,
    current_user: User = Depends(get_current_user),
    repo: UserRepository = Depends(get_user_repo),
) -> dict:
    """
    Allows any authenticated user to rotate their own password.

    Args:
        data: UserPasswordChange schema containing current and new passwords.
        current_user: Authenticated user.
        repo: Injected UserRepository instance.

    Returns:
        dict: Success status and message.

    Raises:
        HTTPException(400): If the current password does not verify.
    """
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le mot de passe actuel renseigné est incorrect.",
        )

    repo.update_password(current_user.username, data.new_password, must_change=False)
    return {"status": "success", "message": "Votre mot de passe a été modifié avec succès."}

# =========================================================================
# User Administration Endpoints (RBAC: ADMIN role required)
# =========================================================================

@auth_router.get(
    "/users",
    response_model=List[UserPublic],
    dependencies=[Depends(require_role([UserRole.ADMIN]))],
)
def list_users(repo: UserRepository = Depends(get_user_repo)) -> List[UserPublic]:
    """
    Lists all registered user accounts (Admin privilege required).

    Args:
        repo: Injected UserRepository instance.

    Returns:
        List[UserPublic]: Safe public user profile listings.
    """
    return repo.list_users()

@auth_router.post(
    "/users",
    response_model=UserPublic,
    dependencies=[Depends(require_role([UserRole.ADMIN]))],
)
def create_user(
    user_in: UserCreate,
    repo: UserRepository = Depends(get_user_repo),
) -> UserPublic:
    """
    Creates a new user account with assigned RBAC role (Admin privilege required).

    Args:
        user_in: UserCreate payload.
        repo: Injected UserRepository instance.

    Returns:
        UserPublic: Created user public profile.

    Raises:
        HTTPException(400): If username is duplicate or invalid.
    """
    try:
        return repo.create_user(user_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@auth_router.delete(
    "/users/{username}",
    dependencies=[Depends(require_role([UserRole.ADMIN]))],
)
def delete_user(
    username: str,
    repo: UserRepository = Depends(get_user_repo),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Deletes a user account from the system (Admin privilege required).

    Prohibits self-deletion and forbids deleting the last active system administrator.

    Args:
        username: Target username to delete.
        repo: Injected UserRepository instance.
        current_user: Current authenticated admin.

    Returns:
        dict: Deletion confirmation.

    Raises:
        HTTPException(400): If attempting self-deletion or removing the last admin.
        HTTPException(404): If user does not exist.
    """
    if username.strip().lower() == current_user.username.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous ne pouvez pas supprimer votre propre compte administrateur connecté.",
        )

    try:
        success = repo.delete_user(username)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")
        return {"status": "deleted", "username": username}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@auth_router.post(
    "/users/{username}/reset-password",
    dependencies=[Depends(require_role([UserRole.ADMIN]))],
)
def reset_user_password(
    username: str,
    data: UserPasswordReset,
    repo: UserRepository = Depends(get_user_repo),
) -> dict:
    """
    Resets a user's password by administrator, setting forced change on next login.

    Args:
        username: Target username.
        data: UserPasswordReset payload with new password.
        repo: Injected UserRepository instance.

    Returns:
        dict: Reset confirmation message.

    Raises:
        HTTPException(404): If user does not exist.
    """
    user = repo.get_user(username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")

    repo.update_password(username, data.new_password, must_change=True)
    return {
        "status": "success",
        "message": f"Mot de passe réinitialisé pour '{username}'. L'utilisateur devra le changer à la prochaine connexion.",
    }
