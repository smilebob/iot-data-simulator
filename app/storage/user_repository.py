import json
import logging
import os
import stat
import tempfile
import threading
from datetime import datetime
from typing import Dict, List, Optional

from app.core.security import hash_password
from app.models.user import User, UserCreate, UserPublic, UserRole

logger = logging.getLogger("iot_sim.users")

class UserRepository:
    """
    Gestionnaire de persistance thread-safe pour les utilisateurs et l'authentification.
    Stocke les données dans un fichier dédié 'data/users.json' avec permissions restreintes (0600),
    séparé du fichier de scénario 'simulator_state.json' pour empêcher la fuite de secrets.
    """

    def __init__(self, file_path: str = "data/users.json"):
        self.file_path = file_path
        self._lock = threading.Lock()
        self.users: Dict[str, User] = {}
        self.load()

    def load(self):
        with self._lock:
            if not os.path.exists(self.file_path):
                logger.info(f"Fichier utilisateurs inexistant ({self.file_path}), initialisation du compte administrateur par défaut.")
                self._bootstrap_default_admin()
                self._save_unsafe()
                return

            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)

                self.users.clear()
                for item in raw_data.get("users", []):
                    u = User.model_validate(item)
                    self.users[u.username] = u

                # Si aucun admin présent, recréer l'admin par défaut
                if not any(u.role == UserRole.ADMIN and u.is_active for u in self.users.values()):
                    logger.warning("Aucun administrateur actif trouvé, création du compte administrateur par défaut.")
                    self._bootstrap_default_admin()
                    self._save_unsafe()

                logger.info(f"Chargé {len(self.users)} utilisateur(s) depuis {self.file_path}")
            except Exception as e:
                logger.error(f"Erreur chargement utilisateurs depuis {self.file_path}: {e}")
                self._bootstrap_default_admin()
                self._save_unsafe()

    def _bootstrap_default_admin(self):
        """Initialise le compte administrateur par défaut selon l'Option A validée."""
        default_user = os.getenv("DEFAULT_ADMIN_USERNAME", "admin").strip().lower()
        default_pass = os.getenv("DEFAULT_ADMIN_PASSWORD", "Admin_123456!")

        admin_user = User(
            username=default_user,
            full_name="Administrateur Système",
            role=UserRole.ADMIN,
            password_hash=hash_password(default_pass),
            created_at=datetime.utcnow().isoformat(),
            last_login=None,
            is_active=True,
            must_change_password=True,
        )
        self.users[default_user] = admin_user
        logger.info(f"Compte administrateur par défaut initialisé : '{default_user}'")

    def _save_unsafe(self):
        """Sauvegarde atomique thread-unsafe avec permissions strictes 0600 (CIS Benchmark)."""
        data = {
            "users": [u.model_dump() for u in self.users.values()]
        }

        dir_name = os.path.dirname(self.file_path) or "."
        os.makedirs(dir_name, exist_ok=True)

        temp_fd, temp_path = tempfile.mkstemp(dir=dir_name, prefix="users_tmp_")
        try:
            with open(temp_fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Application stricte des permissions 0600 (lecture/écriture seul par le propriétaire)
            os.chmod(temp_path, stat.S_IRUSR | stat.S_IWUSR)
            os.replace(temp_path, self.file_path)
            # Réapplication sur le fichier final
            try:
                os.chmod(self.file_path, stat.S_IRUSR | stat.S_IWUSR)
            except Exception:
                pass
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e

    def save(self):
        """Sauvegarde atomique thread-safe."""
        with self._lock:
            self._save_unsafe()

    def get_user(self, username: str) -> Optional[User]:
        with self._lock:
            return self.users.get(username.strip().lower())

    def list_users(self) -> List[UserPublic]:
        with self._lock:
            return [
                UserPublic(
                    username=u.username,
                    full_name=u.full_name,
                    role=u.role,
                    created_at=u.created_at,
                    last_login=u.last_login,
                    is_active=u.is_active,
                    must_change_password=u.must_change_password,
                )
                for u in sorted(self.users.values(), key=lambda x: x.username)
            ]

    def create_user(self, user_in: UserCreate) -> UserPublic:
        with self._lock:
            username = user_in.username.strip().lower()
            if username in self.users:
                raise ValueError(f"L'identifiant '{username}' est déjà utilisé.")

            new_user = User(
                username=username,
                full_name=user_in.full_name.strip(),
                role=user_in.role,
                password_hash=hash_password(user_in.password),
                created_at=datetime.utcnow().isoformat(),
                last_login=None,
                is_active=True,
                must_change_password=False,
            )
            self.users[username] = new_user
            self._save_unsafe()
            logger.info(f"Utilisateur '{username}' créé avec le rôle '{user_in.role.value}'")

            return UserPublic(
                username=new_user.username,
                full_name=new_user.full_name,
                role=new_user.role,
                created_at=new_user.created_at,
                last_login=new_user.last_login,
                is_active=new_user.is_active,
                must_change_password=new_user.must_change_password,
            )

    def update_password(self, username: str, new_password: str, must_change: bool = False) -> bool:
        with self._lock:
            u = self.users.get(username.strip().lower())
            if not u:
                return False

            u.password_hash = hash_password(new_password)
            u.must_change_password = must_change
            self._save_unsafe()
            logger.info(f"Mot de passe mis à jour pour l'utilisateur '{username}'")
            return True

    def update_last_login(self, username: str):
        with self._lock:
            u = self.users.get(username.strip().lower())
            if u:
                u.last_login = datetime.utcnow().isoformat()
                try:
                    self._save_unsafe()
                except Exception as e:
                    logger.warning(f"Erreur mise à jour last_login: {e}")

    def delete_user(self, username: str) -> bool:
        with self._lock:
            uname = username.strip().lower()
            if uname not in self.users:
                return False

            target = self.users[uname]
            if target.role == UserRole.ADMIN:
                # Vérifier qu'il reste au moins un autre administrateur actif
                other_admins = [
                    u for u in self.users.values()
                    if u.username != uname and u.role == UserRole.ADMIN and u.is_active
                ]
                if not other_admins:
                    raise ValueError("Impossible de supprimer le dernier compte administrateur du système.")

            del self.users[uname]
            self._save_unsafe()
            logger.info(f"Utilisateur '{uname}' supprimé du système.")
            return True
