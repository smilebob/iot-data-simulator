import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.routes import router as api_router
from app.api.websocket import WebSocketManager
from app.core.engine import SimulationEngine
from app.mqtt.client import MqttManager
from app.storage.repository import StorageRepository
from app.core.logger import log_handler

# Configuration du Logging standard
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
)
logger = logging.getLogger("iot_sim")

# Version officielle de l'application
APP_VERSION = "1.3.0"

# Initialisation des instances globales
repository = StorageRepository(file_path="data/simulator_state.json")
mqtt_manager = MqttManager(repository.get_broker())
from app.transports.manager import TransportManager
transport_manager = TransportManager(repository, mqtt_manager)
engine = SimulationEngine(repository, mqtt_manager, transport_manager)
ws_manager = WebSocketManager()

# Connexion de la boucle de simulation au WebSocket
def ws_broadcaster(msg: dict):
    asyncio.create_task(ws_manager.broadcast_json(msg))

engine.register_ws_broadcast(ws_broadcaster)
log_handler.set_broadcast_callback(ws_broadcaster)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Démarrage
    logger.info(f"Démarrage de la stack IoT Data Simulator (v{APP_VERSION})...")
    mqtt_manager.start()
    engine.start()
    yield
    # Arrêt propre
    logger.info("Arrêt des services...")
    engine.stop()
    mqtt_manager.stop_all()

app = FastAPI(
    title="IoT Data Simulator for ThingsBoard & Multi-Platform",
    version=APP_VERSION,
    description="Simulateur IoT industriel sécurisé, modulaire et conforme CIS",
    lifespan=lifespan,
)

# Middleware de sécurité (CIS / OWASP Best Practices)
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Configuration CORS sécurisée
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Endpoints API & Healthcheck (requis pour le CIS Docker Benchmark Rule 4.6)
@app.get("/healthz")
def healthcheck():
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "engine_running": engine.is_running,
        "mqtt_connected": mqtt_manager.default_client.is_connected if mqtt_manager.default_client else False,
    }

app.include_router(api_router)

# WebSocket pour télémétrie en temps réel
@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Réception de messages ping ou commandes client
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)

# Montage des fichiers statiques de l'interface GUI
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
def get_index():
    return FileResponse("app/static/index.html")
