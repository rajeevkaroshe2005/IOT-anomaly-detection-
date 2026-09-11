"""
FastAPI Main Application Entry Point
Cloud-Based Real-Time IoT Sensor Monitoring & Anomaly Detection System
"""

import os
import sys
import asyncio
import logging
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.services.security import decode_access_token

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configure Structured Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("iot.main")

from backend.database.seed_data import seed_database_if_empty
from backend.ml.ml_model import ml_detector
from backend.services.stream_processor import stream_processor
from backend.services.websocket_manager import ws_manager
from backend.services.simulator_service import simulator_service
from backend.mqtt.mqtt_client import mqtt_service

# Import API Routers
from backend.routes.auth import router as auth_router
from backend.routes.sensors import router as sensors_router
from backend.routes.readings import router as readings_router
from backend.routes.anomalies import router as anomalies_router
from backend.routes.alerts import router as alerts_router
from backend.routes.dashboard import router as dashboard_router
from backend.routes.system import router as system_router
from backend.routes.simulator import router as simulator_router
from backend.routes.predictive import router as predictive_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup Lifecycle ---
    logger.info("Initializing Cloud IoT Monitoring Backend...")
    
    # 1. Ensure DB tables and default demo seeds exist
    seed_database_if_empty()
    
    # 2. Ensure ML model is loaded and preheated
    ml_detector.load_or_train()
    
    # 3. Associate running async loop with stream processor for WebSocket broadcasts
    loop = asyncio.get_running_loop()
    stream_processor.set_event_loop(loop)
    
    # 4. Start MQTT Background Supervisor
    mqtt_service.start()
    
    # 5. Check if simulator autorun is enabled
    if os.getenv("SIMULATOR_AUTORUN", "False").lower() in ("true", "1", "yes"):
        logger.info("Auto-starting sensor simulator on boot...")
        simulator_service.start()

    logger.info("FastAPI Backend initialization complete. Ready for real-time telemetry.")
    yield
    
    # --- Shutdown Lifecycle ---
    logger.info("Shutting down backend services...")
    simulator_service.stop()
    mqtt_service.stop()
    logger.info("All background threads safely terminated.")

app = FastAPI(
    title="Cloud-Based IoT Sensor Monitoring & Anomaly Detection API",
    description="Real-time MQTT telemetry ingestion, Scikit-learn Isolation Forest anomaly detection, and WebSocket broadcasting.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for React/Vite development and container environments
cors_env = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:5174,http://127.0.0.1:5175,http://127.0.0.1:3000"
)
allowed_origins = [origin.strip() for origin in cors_env.split(",") if origin.strip()]
if not allowed_origins:
    allowed_origins = ["http://localhost:5173", "http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router)
app.include_router(sensors_router)
app.include_router(readings_router)
app.include_router(anomalies_router)
app.include_router(alerts_router)
app.include_router(dashboard_router)
app.include_router(system_router)
app.include_router(simulator_router)
app.include_router(predictive_router)

# WebSocket Real-Time Telemetry Endpoint
@app.websocket("/ws/sensor-data")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = Query(None)):
    """
    Real-Time WebSocket Channel:
    Streams live sensor telemetry, anomaly detections, alerts, and system state directly to connected web clients.
    Secured with signed JWT token query parameter. Unauthenticated connections are closed with code 1008 (Policy Violation).
    """
    if not token:
        logger.warning("WebSocket handshake rejected: missing authentication token")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        logger.warning("WebSocket handshake rejected: invalid or expired token")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and accept client commands (e.g. ping/subscribe)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"event": "pong"}')
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket client error: {e}")
        await ws_manager.disconnect(websocket)

# Root Health probe
@app.get("/")
def root():
    return {
        "status": "online",
        "service": "Cloud-Based Real-Time IoT Sensor Monitoring & Anomaly Detection System",
        "version": "1.0.0",
        "docs_url": "/docs",
        "websocket_url": "/ws/sensor-data"
    }

if __name__ == "__main__":
    import uvicorn
    reload_flag = os.getenv("APP_ENV", "development").lower() == "development"
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=reload_flag)
