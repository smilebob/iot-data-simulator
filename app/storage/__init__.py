"""
Persistent storage repositories for simulation models and user credentials.

This package provides:
- `StorageRepository`: Thread-safe persistence of devices, variables, and broker configuration.
- `UserRepository`: Thread-safe RBAC user accounts repository with POSIX 0600 file permissions.
"""

from app.storage.repository import StorageRepository
from app.storage.user_repository import UserRepository

__all__ = ["StorageRepository", "UserRepository"]
