"""
FastAPI Application Entrypoint and Lifecycle Orchestrator.

This module initializes the core web server, mounts API routers and static web assets,
enforces CIS/OWASP security headers, and orchestrates background simulation runtimes:
- `lifespan`: Async context manager starting and gracefully stopping the MQTT connection pool
  and the real-time simulation engine loop.
- `SecurityHeadersMiddleware`: Injects hardened HTTP response headers (nosniff, DENY, referrer-policy).
- `/healthz`: Comprehensive container readiness and liveness health check endpoint
  conforming to CIS Docker Benchmark Rule 4.6.
- `/ws/live`: Authenticated WebSocket stream for real-time telemetry, log records, and RPC events.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.auth import auth_router
from app.api.routes import router as api_router
from app.api.websocket import WebSocketManager
from app.core.engine import SimulationEngine
from app.core.logger import log_handler
from app.core.security import decode_jwt_token
from app.mqtt.client import MqttManager
from app.storage.repository import StorageRepository
from app.storage.user_repository import UserRepository
from app.transports.manager import TransportManager

# Configure standard console logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
)
logger = logging.getLogger("iot_sim")

# Official semantic version of the application
APP_VERSION = "2.2.1"

# Initialize application-wide singletons
repository = StorageRepository(file_path="data/simulator_state.json")
user_repository = UserRepository(file_path="data/users.json")
mqtt_manager = MqttManager(repository.get_broker())
transport_manager = TransportManager(repository, mqtt_manager)
engine = SimulationEngine(repository, mqtt_manager, transport_manager)
ws_manager = WebSocketManager()

# Bridge simulation and logging events to connected WebSocket clients
def ws_broadcaster(msg: dict) -> None:
    """Dispatches a dictionary message to all active WebSocket clients via async task."""
    asyncio.create_task(ws_manager.broadcast_json(msg))

engine.register_ws_broadcast(ws_broadcaster)
log_handler.set_broadcast_callback(ws_broadcaster)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages startup and shutdown lifecycle hooks of the FastAPI application.

    Starts MQTT background connections and kicks off the 3-pass causal simulation loop.
    On application teardown, stops all background workers and disconnects cleanly.
    """
    logger.info(f"Starting IoT Data Simulator stack (v{APP_VERSION})...")
    mqtt_manager.start()
    engine.start(loop=asyncio.get_running_loop())
    yield
    logger.info("Gracefully stopping simulator services...")
    engine.stop()
    mqtt_manager.stop_all()

app = FastAPI(
    title="IoT Data Simulator for ThingsBoard & Multi-Platform",
    version=APP_VERSION,
    description="Secure, modular, and CIS-compliant industrial IoT simulator stack",
    lifespan=lifespan,
)

# Security Headers Middleware (CIS Docker & OWASP Best Practices)
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects defensive HTTP headers into every outgoing response."""
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Cross-Origin Resource Sharing (CORS) Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Healthcheck & Observability (required by CIS Docker Benchmark Rule 4.6)
@app.get("/healthz")
def healthcheck() -> dict:
    """
    Container readiness and liveness health probe.

    Returns:
        dict: Operational telemetry, running status, device summary, and recent logs.
    """
    devs = []
    for d in repository.get_devices():
        devs.append({
            "id": d.id,
            "name": d.name,
            "platform": getattr(d.platform, "value", str(d.platform)),
            "protocol": getattr(d.protocol, "value", str(d.protocol)),
            "has_token": bool(d.token),
            "token_preview": (d.token[:4] + "***") if d.token else None,
            "custom_host": d.custom_host,
            "enabled": d.enabled,
        })
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "engine_running": engine.is_running,
        "mqtt_connected": mqtt_manager.default_client.is_connected if mqtt_manager.default_client else False,
        "devices": devs,
        "http_rpc_listeners": list(engine._http_rpc_tasks.keys()),
        "http_attribute_listeners": list(engine._http_attr_tasks.keys()),
        "recent_logs": [entry["message"] for entry in log_handler.get_logs(limit=10)],
    }

app.include_router(auth_router)
app.include_router(api_router)

# Authenticated real-time WebSocket endpoint (JWT verified via Cookie or Query param)
@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    Authenticated WebSocket connection endpoint.

    Validates JWT session credentials before admitting the socket.
    Rejects unauthenticated connections with WS_1008_POLICY_VIOLATION.
    """
    token = websocket.cookies.get("access_token") or websocket.query_params.get("token")
    if not token or not decode_jwt_token(token):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentification requise")
        return

    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)

# Mount frontend web assets
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
def get_index() -> FileResponse:
    """Serves the single-page application index HTML document."""
    return FileResponse("app/static/index.html")

