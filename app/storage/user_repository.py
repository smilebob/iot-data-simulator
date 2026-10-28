"""
User Persistence and RBAC Credentials Repository.

This module manages user profiles, password hashes, and RBAC roles:
- Storage isolation: Stored in a separate dedicated file (`data/users.json`) with restricted
  POSIX file permissions (`0600` - read/write for owner only) conforming to CIS Docker Benchmark
  recommendations. Separated from `simulator_state.json` to prevent leaking hashed secrets during
  scenario exports.
- Atomic write pattern: Uses `tempfile.mkstemp` and `os.replace` to prevent credential corruption.
- Automatic default bootstrap: Creates initial administrator (`admin` / `Admin_123456!`) with
  `must_change_password=True` if no active administrator exists.
- In-memory thread safety: Operations protected by `threading.Lock`.
"""

import json
import logging
import os
import stat
import tempfile
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.core.security import hash_password
from app.models.user import User, UserCreate, UserPublic, UserRole

logger = logging.getLogger("iot_sim.users")

class UserRepository:
    """
    Thread-safe repository managing user accounts, authentication states, and RBAC roles.

    Attributes:
        file_path: Path to the dedicated users JSON file. Defaults to 'data/users.json'.
        users: In-memory dictionary mapping lowercased usernames to User models.
    """

    def __init__(self, file_path: str = "data/users.json") -> None:
        """
        Initializes the user repository and loads accounts from storage.

        Args:
            file_path: Filesystem path to users file. Defaults to 'data/users.json'.
        """
        self.file_path: str = file_path
        self._lock: threading.Lock = threading.Lock()
        self.users: Dict[str, User] = {}
        self.load()

    def load(self) -> None:
        """
        Loads user profiles from persistent storage.

        If the file does not exist, or contains no active administrator,
        bootstraps the default admin account.
        """
        with self._lock:
            if not os.path.exists(self.file_path):
                logger.info(f"Users file does not exist ({self.file_path}); bootstrapping default admin account.")
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

                # Ensure at least one active administrator exists
                if not any(u.role == UserRole.ADMIN and u.is_active for u in self.users.values()):
                    logger.warning("No active administrator found; bootstrapping default admin account.")
                    self._bootstrap_default_admin()
                    self._save_unsafe()

                logger.info(f"Loaded {len(self.users)} user account(s) from {self.file_path}")
            except Exception as e:
                logger.error(f"Error loading users from {self.file_path}: {e}")
                self._bootstrap_default_admin()
                self._save_unsafe()

    def _bootstrap_default_admin(self) -> None:
        """Initializes default administrative account with forced initial password rotation."""
        default_user = os.getenv("DEFAULT_ADMIN_USERNAME", "admin").strip().lower()
        default_pass = os.getenv("DEFAULT_ADMIN_PASSWORD", "Admin_123456!")

        admin_user = User(
            username=default_user,
            full_name="Administrateur Système",
            role=UserRole.ADMIN,
            password_hash=hash_password(default_pass),
            created_at=datetime.now(timezone.utc).isoformat(),
            last_login=None,
            is_active=True,
            must_change_password=True,
        )
        self.users[default_user] = admin_user
        logger.info(f"Default admin account initialized: '{default_user}'")

    def _save_unsafe(self) -> None:
        """Atomic write with POSIX 0600 file permissions (owner read/write only)."""
        data = {
            "users": [u.model_dump() for u in self.users.values()]
        }

        dir_name = os.path.dirname(self.file_path) or "."
        os.makedirs(dir_name, exist_ok=True)

        temp_fd, temp_path = tempfile.mkstemp(dir=dir_name, prefix="users_tmp_")
        try:
            with open(temp_fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Enforce strict 0600 permissions
            os.chmod(temp_path, stat.S_IRUSR | stat.S_IWUSR)
            os.replace(temp_path, self.file_path)
            try:
                os.chmod(self.file_path, stat.S_IRUSR | stat.S_IWUSR)
            except Exception:
                pass
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e

    def save(self) -> None:
        """Thread-safe user state persistence."""
        with self._lock:
            self._save_unsafe()

    def get_user(self, username: str) -> Optional[User]:
        """
        Retrieves a user by username (case-insensitive).

        Args:
            username: User login identifier.

        Returns:
            Optional[User]: User model instance with password hash, or None.
        """
        with self._lock:
            return self.users.get(username.strip().lower())

    def list_users(self) -> List[UserPublic]:
        """
        Lists all users without exposing password hashes.

        Returns:
            List[UserPublic]: List of safe public user representations sorted alphabetically.
        """
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
        """
        Registers a new user account with hashed credentials.

        Args:
            user_in: User creation schema.

        Returns:
            UserPublic: Public representation of created user.

        Raises:
            ValueError: If the username already exists.
        """
        with self._lock:
            username = user_in.username.strip().lower()
            if username in self.users:
                raise ValueError(f"L'identifiant '{username}' est déjà utilisé.")

            new_user = User(
                username=username,
                full_name=user_in.full_name.strip(),
                role=user_in.role,
                password_hash=hash_password(user_in.password),
                created_at=datetime.now(timezone.utc).isoformat(),
                last_login=None,
                is_active=True,
                must_change_password=False,
            )
            self.users[username] = new_user
            self._save_unsafe()
            logger.info(f"User '{username}' created with role '{user_in.role.value}'")

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
        """
        Updates a user's password with a newly computed Scrypt hash.

        Args:
            username: Target user identifier.
            new_password: New plaintext password.
            must_change: Whether to force password rotation on next login.

        Returns:
            bool: True if user was found and updated, False otherwise.
        """
        with self._lock:
            u = self.users.get(username.strip().lower())
            if not u:
                return False

            u.password_hash = hash_password(new_password)
            u.must_change_password = must_change
            self._save_unsafe()
            logger.info(f"Password updated for user '{username}'")
            return True

    def update_last_login(self, username: str) -> None:
        """
        Records current UTC timestamp as the user's latest login time.

        Args:
            username: Target user identifier.
        """
        with self._lock:
            u = self.users.get(username.strip().lower())
            if u:
                u.last_login = datetime.now(timezone.utc).isoformat()
                try:
                    self._save_unsafe()
                except Exception as e:
                    logger.warning(f"Error updating last_login: {e}")

    def delete_user(self, username: str) -> bool:
        """
        Deletes a user account.

        Guarantees system safety by forbidding deletion of the last remaining active administrator.

        Args:
            username: User identifier to remove.

        Returns:
            bool: True if deleted, False if user does not exist.

        Raises:
            ValueError: If attempting to delete the last active administrator.
        """
        with self._lock:
            uname = username.strip().lower()
            if uname not in self.users:
                return False

            target = self.users[uname]
            if target.role == UserRole.ADMIN:
                other_admins = [
                    u for u in self.users.values()
                    if u.username != uname and u.role == UserRole.ADMIN and u.is_active
                ]
                if not other_admins:
                    raise ValueError("Impossible de supprimer le dernier compte administrateur du système.")

            del self.users[uname]
            self._save_unsafe()
            logger.info(f"User '{uname}' deleted from system.")
            return True
