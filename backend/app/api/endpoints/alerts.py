from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.database import get_db
from app.services.alert_service import AlertService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def get_alerts(
    ticker: Optional[str] = Query(None),
    severity: Optional[str] = Query(None, regex="^(low|medium|high|critical)$"),
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get system alerts"""
    try:
        alert_service = AlertService(db)
        alerts = alert_service.get_alerts(
            ticker=ticker,
            severity=severity,
            unread_only=unread_only,
            limit=limit
        )
        return alerts
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{ticker}")
async def get_company_alerts(
    ticker: str,
    days: int = Query(7, ge=1, le=30),
    severity: Optional[str] = Query(None, regex="^(low|medium|high|critical)$"),
    db: Session = Depends(get_db)
):
    """Get alerts for a specific company"""
    try:
        alert_service = AlertService(db)
        alerts = alert_service.get_company_alerts(ticker, days=days, severity=severity)
        if not alerts:
            raise HTTPException(status_code=404, detail="Alerts not found")
        return alerts
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching alerts for {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{alert_id}/read")
async def mark_alert_read(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """Mark an alert as read"""
    try:
        alert_service = AlertService(db)
        success = alert_service.mark_alert_read(alert_id)
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        return {"message": "Alert marked as read"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking alert {alert_id} as read: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    acknowledged_by: str,
    db: Session = Depends(get_db)
):
    """Acknowledge an alert"""
    try:
        alert_service = AlertService(db)
        success = alert_service.acknowledge_alert(alert_id, acknowledged_by)
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        return {"message": "Alert acknowledged"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/summary")
async def get_alerts_summary(db: Session = Depends(get_db)):
    """Get alerts summary statistics"""
    try:
        alert_service = AlertService(db)
        summary = alert_service.get_alerts_summary()
        return summary
    except Exception as e:
        logger.error(f"Error fetching alerts summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")




