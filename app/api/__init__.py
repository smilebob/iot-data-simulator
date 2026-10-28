"""
REST API routers, WebSocket streaming handlers, and authentication providers.

This package provides:
- `routes`: CRUD endpoints for devices, variables, MQTT broker, and simulation state.
- `auth`: JWT authentication, HttpOnly cookies, and RBAC role dependencies.
- `websocket`: Asynchronous broadcast pool for real-time telemetry and logging.
"""

from app.api.auth import auth_router, get_current_user, require_role
from app.api.routes import router as api_router
from app.api.websocket import WebSocketManager

__all__ = ["api_router", "auth_router", "get_current_user", "require_role", "WebSocketManager"]
