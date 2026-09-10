"""
Predictive Maintenance & Health Forecasting Router
"""

from fastapi import APIRouter
from backend.services.predictive_service import predictive_service

router = APIRouter(prefix="/api/predictive", tags=["Predictive Analytics"])

@router.get("/analytics")
def get_predictive_analytics():
    return predictive_service.get_fleet_analytics()

@router.get("/sensor/{sensor_id}")
def get_sensor_prediction(sensor_id: int):
    return predictive_service.analyze_sensor_trajectory(sensor_id)
