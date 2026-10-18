# File: backend/app/utils/websocket_manager.py
# Description: Real-time WebSocket connection manager for live district telemetry, alerts broadcast, and OPD queues

import json
import logging
from typing import List
from fastapi import WebSocket

logger = logging.getLogger("swasthya.ws")

class WebSocketConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total active: {len(self.active_connections)}")

    async def broadcast_json(self, data: dict):
        """Broadcasts live event to all connected dashboard and mobile clients"""
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(data))
            except Exception:
                dead_connections.append(connection)
                
        for dead in dead_connections:
            if dead in self.active_connections:
                self.active_connections.remove(dead)

ws_manager = WebSocketConnectionManager()

