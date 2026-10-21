import asyncio
import logging
from typing import List
from fastapi import WebSocket

logger = logging.getLogger("iot_sim.ws")

class WebSocketManager:
    """Gestionnaire de connexions WebSockets pour la diffusion temps réel."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.debug(f"Client WebSocket connecté. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.debug(f"Client WebSocket déconnecté. Total: {len(self.active_connections)}")

    async def broadcast_json(self, message: dict):
        if not self.active_connections:
            return
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)
