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
from backend.services.auth_service import require_auth, require_admin, get_current_user, get_user_from_token_str

router = APIRouter(prefix="/api/anomalies", tags=["Anomalies"])

@router.get("", response_model=List[AnomalyResponse])
def get_anomalies(
    sensor_id: Optional[int] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
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

@router.get("/export/csv")
def export_anomalies_csv(
    sensor_id: Optional[int] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(500, ge=1, le=5000),
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user)
):
    """Exports detected anomalies to downloadable CSV format (requires authentication)."""
    authenticated_user = user or (get_user_from_token_str(token, db) if token else None)
    if not authenticated_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to export anomalies."
        )

    import io
    import csv
    from datetime import datetime, timezone
    from fastapi.responses import Response

    query = db.query(Anomaly)
    if sensor_id is not None:
        query = query.filter(Anomaly.sensor_id == sensor_id)
    if severity:
        query = query.filter(Anomaly.severity == severity.upper())

    anomalies = query.order_by(desc(Anomaly.timestamp)).limit(limit).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Anomaly_ID", "Device_ID", "Sensor_Name", "Location",
        "Temperature_C", "Humidity_Pct", "Pressure_hPa",
        "Anomaly_Score", "Severity", "Reason", "Timestamp_UTC", "Acknowledged"
    ])

    for a in anomalies:
        writer.writerow([
            a.id,
            a.sensor.device_id if a.sensor else "",
            a.sensor.name if a.sensor else "",
            a.sensor.location if a.sensor else "",
            a.temperature,
            a.humidity,
            a.pressure,
            a.anomaly_score,
            a.severity,
            a.reason or "",
            a.timestamp.isoformat() if a.timestamp else "",
            a.acknowledged
        ])

    csv_content = output.getvalue()
    filename = f"industrial_anomalies_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
