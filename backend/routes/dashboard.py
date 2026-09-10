"""
Dashboard Dynamic Aggregation Endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.database.database import get_db
from backend.database.models import Sensor, SensorReading, Alert
from backend.schemas.schemas import DashboardStats
from backend.services.simulator_service import simulator_service

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_sensors = db.query(Sensor).count()
    online_sensors = db.query(Sensor).filter(Sensor.status == "ONLINE", Sensor.is_enabled == True).count()
    offline_sensors = total_sensors - online_sensors

    total_readings = db.query(SensorReading).count()
    total_anomalies = db.query(SensorReading).filter(SensorReading.is_anomaly == True).count()
    active_alerts = db.query(Alert).filter(Alert.status == "ACTIVE").count()

    # Dynamic system health calculation
    # Base 100%, deduct 4% per offline sensor, 2% per active alert
    penalty = (offline_sensors * 4.0) + (active_alerts * 2.0)
    health_pct = max(70.0, min(100.0, 100.0 - penalty))

    latest_entity = db.query(SensorReading).order_by(desc(SensorReading.timestamp)).first()
    latest_dict = latest_entity.to_dict() if latest_entity else None

    return {
        "total_sensors": total_sensors,
        "online_sensors": online_sensors,
        "offline_sensors": offline_sensors,
        "total_readings": total_readings,
        "total_anomalies": total_anomalies,
        "active_alerts": active_alerts,
        "system_health_pct": round(health_pct, 1),
        "latest_reading": latest_dict,
        "simulator_running": simulator_service.is_running
    }
