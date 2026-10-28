"""
WebSocket Connection Manager for Real-Time Telemetry and Log Streaming.

This module provides an asynchronous connection pool managing all active WebSocket
clients connected to `/ws`. It broadcasts:
- Live telemetry and attribute evaluations (`{"type": "telemetry", ...}`)
- Log events and status alerts (`{"type": "log", ...}`)
- Simulation engine state transitions (`{"type": "state", ...}`)
- Dead connection pruning and resource reclamation.
"""

import asyncio
import logging
from typing import List
from fastapi import WebSocket

logger = logging.getLogger("iot_sim.ws")

class WebSocketManager:
    """
    Asynchronous connection manager and broadcaster for WebSocket clients.

    Attributes:
        active_connections: List of actively connected WebSocket sockets.
    """

    def __init__(self) -> None:
        """Initializes empty connection pool."""
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """
        Accepts and registers a new incoming WebSocket connection.

        Args:
            websocket: FastAPI WebSocket instance.
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.debug(f"WebSocket client connected. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Removes a disconnected WebSocket from the connection pool.

        Args:
            websocket: FastAPI WebSocket instance.
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.debug(f"WebSocket client disconnected. Total active: {len(self.active_connections)}")

    async def broadcast_json(self, message: dict) -> None:
        """
        Broadcasts a JSON dictionary payload to all connected clients.

        Gracefully detects disconnected sockets and prunes them from the pool.

        Args:
            message: Serializable dictionary payload to broadcast.
        """
        if not self.active_connections:
            return
        dead_connections: List[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)

