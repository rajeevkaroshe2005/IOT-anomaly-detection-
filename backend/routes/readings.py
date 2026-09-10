"""
Sensor Telemetry Readings Endpoints
"""

from typing import List, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from backend.database.database import get_db
from backend.database.models import Sensor, SensorReading
from backend.schemas.schemas import SensorReadingCreate, SensorReadingResponse
from backend.services.stream_processor import stream_processor

router = APIRouter(prefix="/api/readings", tags=["Readings"])

@router.get("", response_model=List[SensorReadingResponse])
def get_readings(
    sensor_id: Optional[int] = Query(None, description="Filter by sensor database ID"),
    limit: int = Query(100, ge=1, le=1000),
    anomalies_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    query = db.query(SensorReading)
    if sensor_id is not None:
        query = query.filter(SensorReading.sensor_id == sensor_id)
    if anomalies_only:
        query = query.filter(SensorReading.is_anomaly == True)

    readings = query.order_by(desc(SensorReading.timestamp)).limit(limit).all()
    return [r.to_dict() for r in readings]

@router.get("/{sensor_id}", response_model=List[SensorReadingResponse])
def get_sensor_readings(
    sensor_id: int,
    timeframe: str = Query("30m", description="Time window: 1m, 5m, 30m, 1h, 24h, all"),
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor not found")

    now = datetime.now(timezone.utc)
    query = db.query(SensorReading).filter(SensorReading.sensor_id == sensor_id)

    if timeframe == "1m":
        cutoff = now - timedelta(minutes=1)
        query = query.filter(SensorReading.timestamp >= cutoff)
    elif timeframe == "5m":
        cutoff = now - timedelta(minutes=5)
        query = query.filter(SensorReading.timestamp >= cutoff)
    elif timeframe == "30m":
        cutoff = now - timedelta(minutes=30)
        query = query.filter(SensorReading.timestamp >= cutoff)
    elif timeframe == "1h":
        cutoff = now - timedelta(hours=1)
        query = query.filter(SensorReading.timestamp >= cutoff)
    elif timeframe == "24h":
        cutoff = now - timedelta(hours=24)
        query = query.filter(SensorReading.timestamp >= cutoff)

    # Return chronological order (ascending) for charts
    readings = query.order_by(asc(SensorReading.timestamp)).limit(limit).all()
    return [r.to_dict() for r in readings]

@router.post("/ingest", response_model=dict, status_code=status.HTTP_200_OK)
def direct_ingest_reading(reading: SensorReadingCreate):
    """
    Direct HTTP ingestion bridge. Feeds into the same Stream Processing pipeline as MQTT.
    """
    payload = reading.model_dump()
    result = stream_processor.process_reading(payload)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Pipeline rejected payload: validation or database failure."
        )
    return {"status": "ingested", "data": result}
