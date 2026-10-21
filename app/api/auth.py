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

# Dépendance UserRepository injectée depuis main.py
def get_user_repo() -> UserRepository:
    from app.main import user_repository
    return user_repository

def get_current_user(
    request: Request,
    access_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None),
    repo: UserRepository = Depends(get_user_repo),
) -> User:
    """
    Extrait et valide le jeton de session JWT depuis le Cookie HTTP-Only ou l'en-tête Authorization.
    """
    token = None
    # 1. Vérification du Cookie sécurisé HttpOnly
    if access_token:
        token = access_token
    # 2. Vérification de l'en-tête Bearer alternatif
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
    Générateur de dépendance RBAC validant que l'utilisateur possède l'un des rôles requis.
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
# Endpoints Authentification & Session Utilisateur
# =========================================================================

@auth_router.post("/auth/login", response_model=LoginResponse)
def login(
    req: LoginRequest,
    response: Response,
    repo: UserRepository = Depends(get_user_repo),
):
    """
    Authentifie l'utilisateur, vérifie le mot de passe Scrypt et émet un Cookie HTTP-Only.
    """
    user = repo.get_user(req.username)
    if not user or not verify_password(req.password, user.password_hash):
        logger.warning(f"Tentative de connexion échouée pour l'identifiant '{req.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiant ou mot de passe incorrect.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce compte utilisateur est désactivé.",
        )

    # Création du jeton JWT sécurisé (durée de validité : 8h = 28800s)
    token = create_jwt_token({
        "sub": user.username,
        "role": user.role.value,
        "name": user.full_name,
    }, expires_in_seconds=28800)

    # Enregistrement de la date de connexion
    repo.update_last_login(user.username)

    # Émission du Cookie HTTP-Only conforme CIS / OWASP
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=28800,
        path="/",
    )

    logger.info(f"Connexion réussie pour l'utilisateur '{user.username}' ({user.role.value})")

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
def logout(response: Response):
    """
    Clôture la session en révoquant le cookie d'authentification.
    """
    response.delete_cookie(key="access_token", path="/")
    return {"status": "logged_out", "message": "Déconnexion réussie."}

@auth_router.get("/auth/me", response_model=UserPublic)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Retourne le profil de l'utilisateur actuellement connecté.
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
):
    """
    Permet à tout utilisateur connecté de modifier son propre mot de passe.
    """
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le mot de passe actuel renseigné est incorrect.",
        )

    repo.update_password(current_user.username, data.new_password, must_change=False)
    return {"status": "success", "message": "Votre mot de passe a été modifié avec succès."}

# =========================================================================
# Endpoints Administration des Utilisateurs (RBAC : ADMIN uniquement)
# =========================================================================

@auth_router.get(
    "/users",
    response_model=List[UserPublic],
    dependencies=[Depends(require_role([UserRole.ADMIN]))],
)
def list_users(repo: UserRepository = Depends(get_user_repo)):
    """
    Liste tous les comptes utilisateurs enregistrés (Admin uniquement).
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
):
    """
    Crée un nouvel utilisateur avec son rôle RBAC (Admin uniquement).
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
):
    """
    Supprime un utilisateur du système (Admin uniquement).
    Interdiction absolue de supprimer le dernier compte administrateur.
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
):
    """
    Réinitialise le mot de passe d'un utilisateur par l'administrateur.
    """
    user = repo.get_user(username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")

    repo.update_password(username, data.new_password, must_change=True)
    return {
        "status": "success",
        "message": f"Mot de passe réinitialisé pour '{username}'. L'utilisateur devra le changer à la prochaine connexion.",
    }
