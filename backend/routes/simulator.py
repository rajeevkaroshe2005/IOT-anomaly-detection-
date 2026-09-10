"""
Simulator Control Endpoints
Allows starting, stopping, and triggering anomalies in the background sensor simulator.
"""

from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends
from backend.services.simulator_service import simulator_service
from backend.services.auth_service import require_auth
from backend.database.models import User

router = APIRouter(prefix="/api/simulator", tags=["Simulator"])

class StartSimulatorRequest(BaseModel):
    interval_seconds: Optional[float] = Field(1.5, ge=0.5, le=10.0)
    anomaly_probability: Optional[float] = Field(0.10, ge=0.0, le=1.0)

class ForceAnomalyRequest(BaseModel):
    device_id: Optional[str] = None

@router.post("/start")
def start_simulator(req: Optional[StartSimulatorRequest] = None):
    interval = req.interval_seconds if req else 1.5
    anomaly_prob = req.anomaly_probability if req else 0.10
    return simulator_service.start(interval=interval, anomaly_prob=anomaly_prob)

@router.post("/stop")
def stop_simulator():
    return simulator_service.stop()

@router.get("/status")
def get_simulator_status():
    return simulator_service.get_status()

@router.post("/force-anomaly")
def force_anomaly_injection(req: Optional[ForceAnomalyRequest] = None):
    dev_id = req.device_id if req else None
    result = simulator_service.trigger_forced_anomaly(device_id=dev_id)
    return {"status": "anomaly_injected", "reading": result}
