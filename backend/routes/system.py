"""
System Diagnostics and Audit Log Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.database.database import get_db
from backend.database.models import SystemLog, User
from backend.schemas.schemas import SystemHealthResponse
from backend.services.system_service import get_full_system_health
from backend.services.auth_service import require_admin
from backend.database.seed_data import seed_database_if_empty
from backend.database.database import Base, engine

router = APIRouter(prefix="/api/system", tags=["System"])

@router.get("/health", response_model=SystemHealthResponse)
def get_system_health():
    return get_full_system_health()

@router.get("/logs")
def get_system_logs(
    limit: int = Query(100, ge=1, le=500),
    level: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(SystemLog)
    if level:
        query = query.filter(SystemLog.level == level.upper())
    logs = query.order_by(desc(SystemLog.timestamp)).limit(limit).all()
    return [l.to_dict() for l in logs]

@router.post("/reset-demo", status_code=status.HTTP_200_OK)
def reset_demo_data(admin: User = Depends(require_admin)):
    """Admin utility to wipe and re-seed clean baseline demo data."""
    Base.metadata.drop_all(bind=engine)
    seed_database_if_empty()
    return {"status": "success", "message": "Database successfully reset to initial clean demo state."}
