"""
Pydantic Data Validation & Serialization Schemas
"""

from typing import Optional, List
from pydantic import BaseModel, Field

# ----------------- Auth Schemas -----------------
class UserLogin(BaseModel):
    username: str = Field(..., example="admin")
    password: str = Field(..., example="admin123")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    created_at: Optional[str] = None


# ----------------- Sensor Schemas -----------------
class SensorBase(BaseModel):
    device_id: str = Field(..., min_length=2, max_length=50, example="SENSOR-006")
    name: str = Field(..., min_length=2, max_length=100, example="Chilled Water Pump")
    location: str = Field(..., min_length=2, max_length=100, example="HVAC Plant")
    status: str = Field(default="ONLINE", example="ONLINE")
    is_enabled: bool = True

class SensorCreate(SensorBase):
    pass

class SensorUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    is_enabled: Optional[bool] = None

class SensorResponse(SensorBase):
    id: int
    created_at: Optional[str] = None
    last_seen: Optional[str] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    pressure: Optional[float] = None
    is_anomaly: Optional[bool] = None
    anomaly_score: Optional[float] = None
    last_reading_time: Optional[str] = None


# ----------------- Reading Schemas -----------------
class SensorReadingCreate(BaseModel):
    device_id: str = Field(..., example="SENSOR-001")
    temperature: float = Field(..., ge=-50.0, le=150.0, example=28.5)
    humidity: float = Field(..., ge=0.0, le=100.0, example=52.4)
    pressure: float = Field(..., ge=500.0, le=1500.0, example=1013.25)
    timestamp: Optional[str] = None

class SensorReadingResponse(BaseModel):
    id: int
    sensor_id: int
    device_id: Optional[str] = None
    sensor_name: Optional[str] = None
    location: Optional[str] = None
    temperature: float
    humidity: float
    pressure: float
    timestamp: str
    is_anomaly: bool
    anomaly_score: float


# ----------------- Anomaly Schemas -----------------
class AnomalyResponse(BaseModel):
    id: int
    sensor_id: int
    device_id: Optional[str] = None
    sensor_name: Optional[str] = None
    location: Optional[str] = None
    reading_id: Optional[int] = None
    temperature: float
    humidity: float
    pressure: float
    anomaly_score: float
    severity: str
    reason: Optional[str] = None
    timestamp: str
    acknowledged: bool


# ----------------- Alert Schemas -----------------
class AlertResponse(BaseModel):
    id: int
    sensor_id: int
    device_id: Optional[str] = None
    sensor_name: Optional[str] = None
    location: Optional[str] = None
    type: str
    severity: str
    message: str
    status: str
    created_at: str
    resolved_at: Optional[str] = None


# ----------------- Dashboard & Health -----------------
class DashboardStats(BaseModel):
    total_sensors: int
    online_sensors: int
    offline_sensors: int
    total_readings: int
    total_anomalies: int
    active_alerts: int
    system_health_pct: float
    latest_reading: Optional[SensorReadingResponse] = None
    simulator_running: bool = False

class SubsystemStatus(BaseModel):
    name: str
    status: str  # ONLINE, OFFLINE, WARNING
    latency_ms: Optional[float] = None
    detail: str
    last_checked: str

class SystemHealthResponse(BaseModel):
    overall_status: str
    timestamp: str
    subsystems: List[SubsystemStatus]
    system_metrics: dict


# ----------------- Simulator Schemas -----------------
class SimulatorConfig(BaseModel):
    interval_seconds: float = Field(default=1.5, ge=0.5, le=10.0)
    anomaly_probability: float = Field(default=0.10, ge=0.0, le=1.0)
    burst_mode: bool = False
    target_sensors: Optional[List[str]] = None

class SimulatorStatus(BaseModel):
    is_running: bool
    interval_seconds: float
    anomaly_probability: float
    total_published: int
    last_published_at: Optional[str] = None
