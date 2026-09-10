"""
Alert Management Endpoints
"""

from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.database.database import get_db
from backend.database.models import Alert, User
from backend.schemas.schemas import AlertResponse
from backend.services.auth_service import require_admin
from backend.services.websocket_manager import ws_manager

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])

@router.get("", response_model=List[AlertResponse])
def get_alerts(
    sensor_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    severity: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(Alert)
    if sensor_id is not None:
        query = query.filter(Alert.sensor_id == sensor_id)
    if status_filter:
        query = query.filter(Alert.status == status_filter.upper())
    if severity:
        query = query.filter(Alert.severity == severity.upper())

    alerts = query.order_by(desc(Alert.created_at)).limit(limit).all()
    return [a.to_dict() for a in alerts]

@router.put("/{alert_id}/resolve", response_model=AlertResponse)
def resolve_alert(alert_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    alert.status = "RESOLVED"
    alert.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    
    alert_dict = alert.to_dict()
    ws_manager.broadcast_sync("ALERT_RESOLVED", alert_dict)
    return alert_dict

@router.delete("/{alert_id}", status_code=status.HTTP_200_OK)
def delete_alert(alert_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    db.delete(alert)
    db.commit()
    return {"status": "deleted", "alert_id": alert_id}
