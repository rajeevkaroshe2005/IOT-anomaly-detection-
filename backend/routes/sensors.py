"""
Sensor Management Endpoints
"""

from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.database.database import get_db
from backend.database.models import Sensor, SensorReading, User
from backend.schemas.schemas import SensorCreate, SensorUpdate, SensorResponse
from backend.services.auth_service import require_auth, require_admin

router = APIRouter(prefix="/api/sensors", tags=["Sensors"])

@router.get("", response_model=List[SensorResponse])
def list_sensors(db: Session = Depends(get_db)):
    sensors = db.query(Sensor).all()
    results = []
    for s in sensors:
        latest = (
            db.query(SensorReading)
            .filter(SensorReading.sensor_id == s.id)
            .order_by(desc(SensorReading.timestamp))
            .first()
        )
        results.append(s.to_dict(latest_reading=latest))
    return results

@router.post("", response_model=SensorResponse, status_code=status.HTTP_201_CREATED)
def create_sensor(sensor_in: SensorCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    existing = db.query(Sensor).filter(Sensor.device_id == sensor_in.device_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sensor with Device ID '{sensor_in.device_id}' already exists."
        )

    sensor = Sensor(
        device_id=sensor_in.device_id,
        name=sensor_in.name,
        location=sensor_in.location,
        status=sensor_in.status,
        is_enabled=sensor_in.is_enabled,
        created_at=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc)
    )
    db.add(sensor)
    db.commit()
    db.refresh(sensor)
    return sensor.to_dict()

@router.get("/{sensor_id}", response_model=SensorResponse)
def get_sensor(sensor_id: int, db: Session = Depends(get_db)):
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor not found")

    latest = (
        db.query(SensorReading)
        .filter(SensorReading.sensor_id == sensor.id)
        .order_by(desc(SensorReading.timestamp))
        .first()
    )
    return sensor.to_dict(latest_reading=latest)

@router.put("/{sensor_id}", response_model=SensorResponse)
def update_sensor(sensor_id: int, sensor_in: SensorUpdate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor not found")

    if sensor_in.name is not None:
        sensor.name = sensor_in.name
    if sensor_in.location is not None:
        sensor.location = sensor_in.location
    if sensor_in.status is not None:
        sensor.status = sensor_in.status
    if sensor_in.is_enabled is not None:
        sensor.is_enabled = sensor_in.is_enabled

    db.commit()
    db.refresh(sensor)
    latest = (
        db.query(SensorReading)
        .filter(SensorReading.sensor_id == sensor.id)
        .order_by(desc(SensorReading.timestamp))
        .first()
    )
    return sensor.to_dict(latest_reading=latest)

@router.delete("/{sensor_id}", status_code=status.HTTP_200_OK)
def delete_sensor(sensor_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor not found")

    device_id = sensor.device_id
    db.delete(sensor)
    db.commit()
    return {"status": "deleted", "sensor_id": sensor_id, "device_id": device_id}

@router.post("/{sensor_id}/toggle", response_model=SensorResponse)
def toggle_sensor(sensor_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor not found")

    sensor.is_enabled = not sensor.is_enabled
    sensor.status = "ONLINE" if sensor.is_enabled else "OFFLINE"
    db.commit()
    db.refresh(sensor)
    return sensor.to_dict()
