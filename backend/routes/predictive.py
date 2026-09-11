"""
Predictive Maintenance & Health Forecasting Router
"""

from fastapi import APIRouter, Depends
from backend.services.predictive_service import predictive_service
from backend.services.auth_service import require_auth
from backend.database.models import User

router = APIRouter(prefix="/api/predictive", tags=["Predictive Analytics"])

@router.get("/analytics")
def get_predictive_analytics(current_user: User = Depends(require_auth)):
    return predictive_service.get_fleet_analytics()

@router.get("/sensor/{sensor_id}")
def get_sensor_prediction(sensor_id: int, current_user: User = Depends(require_auth)):
    return predictive_service.analyze_sensor_trajectory(sensor_id)

