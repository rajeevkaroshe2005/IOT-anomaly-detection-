"""
Anomaly Detection Records Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.database.database import get_db
from backend.database.models import Anomaly, User
from backend.schemas.schemas import AnomalyResponse
from backend.services.auth_service import require_admin

router = APIRouter(prefix="/api/anomalies", tags=["Anomalies"])

@router.get("", response_model=List[AnomalyResponse])
def get_anomalies(
    sensor_id: Optional[int] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(Anomaly)
    if sensor_id is not None:
        query = query.filter(Anomaly.sensor_id == sensor_id)
    if severity:
        query = query.filter(Anomaly.severity == severity.upper())

    anomalies = query.order_by(desc(Anomaly.timestamp)).limit(limit).all()
    return [a.to_dict() for a in anomalies]

@router.put("/{anomaly_id}/acknowledge", response_model=AnomalyResponse)
def acknowledge_anomaly(anomaly_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    anomaly = db.query(Anomaly).filter(Anomaly.id == anomaly_id).first()
    if not anomaly:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anomaly record not found")

    anomaly.acknowledged = True
    db.commit()
    db.refresh(anomaly)
    return anomaly.to_dict()
