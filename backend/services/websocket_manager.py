"""
WebSocket Connection Manager for Real-Time Telemetry Broadcasting
Broadcasts: NEW_READING, ANOMALY_DETECTED, ALERT_GENERATED, SENSOR_STATUS, STATS_UPDATE
"""

import asyncio
import json
import logging
from typing import List, Set
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("iot.websocket")

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total active connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total active connections: {len(self.active_connections)}")

    async def broadcast(self, event_type: str, data: dict):
        """Broadcasts a structured JSON payload to all active WebSocket clients."""
        if not self.active_connections:
            return

        message = json.dumps({
            "event": event_type,
            "data": data
        })

        dead_connections: List[WebSocket] = []
        async with self._lock:
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.debug(f"Error sending to websocket client: {e}")
                    dead_connections.append(connection)

            for dead in dead_connections:
                if dead in self.active_connections:
                    self.active_connections.remove(dead)

    def broadcast_sync(self, event_type: str, data: dict, loop=None):
        """Thread-safe synchronous bridge to schedule an async broadcast on the main event loop."""
        if not self.active_connections:
            return

        try:
            if loop and loop.is_running():
                asyncio.run_coroutine_threadsafe(self.broadcast(event_type, data), loop)
            else:
                try:
                    running_loop = asyncio.get_running_loop()
                    running_loop.create_task(self.broadcast(event_type, data))
                except RuntimeError:
                    pass
        except Exception as e:
            logger.error(f"Error scheduling sync broadcast: {e}")

ws_manager = ConnectionManager()
