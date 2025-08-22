from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta

from app.models.alert import Alert
from app.models.company import Company
from app.models.credit_score import CreditScore
from app.core.config import settings

logger = logging.getLogger(__name__)


class AlertService:
    """Service for managing system alerts and notifications"""
    
    def __init__(self, db: Session):
        self.db = db
        self.score_change_threshold = settings.score_change_threshold
        self.alert_time_window = settings.alert_time_window
    
    def get_alerts(self, ticker: Optional[str] = None, severity: Optional[str] = None,
                   unread_only: bool = False, limit: int = 50) -> List[Dict[str, Any]]:
        """Get system alerts with optional filtering"""
        try:
            query = self.db.query(Alert).join(Company)
            
            if ticker:
                query = query.filter(Company.ticker == ticker.upper())
            
            if severity:
                query = query.filter(Alert.severity == severity)
            
            if unread_only:
                query = query.filter(Alert.is_read == False)
            
            alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
            
            return [self._format_alert(alert) for alert in alerts]
            
        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            raise
    
    def get_company_alerts(self, ticker: str, days: int = 7, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get alerts for a specific company"""
        try:
            company = self.db.query(Company).filter(
                Company.ticker == ticker.upper(),
                Company.is_active == True
            ).first()
            
            if not company:
                return []
            
            cutoff_date = datetime.now() - timedelta(days=days)
            query = self.db.query(Alert).filter(
                Alert.company_id == company.id,
                Alert.created_at >= cutoff_date
            )
            
            if severity:
                query = query.filter(Alert.severity == severity)
            
            alerts = query.order_by(Alert.created_at.desc()).all()
            
            return [self._format_alert(alert) for alert in alerts]
            
        except Exception as e:
            logger.error(f"Error getting company alerts for {ticker}: {e}")
            raise
    
    def mark_alert_read(self, alert_id: int) -> bool:
        """Mark an alert as read"""
        try:
            alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
            
            if not alert:
                return False
            
            alert.is_read = True
            self.db.commit()
            
            logger.info(f"Marked alert {alert_id} as read")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error marking alert {alert_id} as read: {e}")
            raise
    
    def acknowledge_alert(self, alert_id: int, acknowledged_by: str) -> bool:
        """Acknowledge an alert"""
        try:
            alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
            
            if not alert:
                return False
            
            alert.is_acknowledged = True
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = datetime.now()
            
            self.db.commit()
            
            logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error acknowledging alert {alert_id}: {e}")
            raise
    
    def get_alerts_summary(self) -> Dict[str, Any]:
        """Get alerts summary statistics"""
        try:
            # Total alerts
            total_alerts = self.db.query(Alert).count()
            
            # Unread alerts
            unread_alerts = self.db.query(Alert).filter(Alert.is_read == False).count()
            
            # Alerts by severity
            severity_counts = self.db.query(
                Alert.severity, self.db.func.count(Alert.id)
            ).group_by(Alert.severity).all()
            
            # Recent alerts (last 24 hours)
            recent_cutoff = datetime.now() - timedelta(hours=24)
            recent_alerts = self.db.query(Alert).filter(
                Alert.created_at >= recent_cutoff
            ).count()
            
            # Alerts by type
            type_counts = self.db.query(
                Alert.alert_type, self.db.func.count(Alert.id)
            ).group_by(Alert.alert_type).all()
            
            return {
                'total_alerts': total_alerts,
                'unread_alerts': unread_alerts,
                'recent_alerts_24h': recent_alerts,
                'severity_distribution': dict(severity_counts),
                'type_distribution': dict(type_counts)
            }
            
        except Exception as e:
            logger.error(f"Error getting alerts summary: {e}")
            raise
    
    def create_score_change_alert(self, company_id: int, previous_score: float, current_score: float) -> Optional[Alert]:
        """Create alert for significant score changes"""
        try:
            score_change = current_score - previous_score
            change_percentage = (score_change / previous_score) * 100 if previous_score > 0 else 0
            
            # Check if change exceeds threshold
            if abs(score_change) < self.score_change_threshold:
                return None
            
            # Determine severity
            if abs(score_change) >= 30:
                severity = "critical"
            elif abs(score_change) >= 20:
                severity = "high"
            elif abs(score_change) >= 10:
                severity = "medium"
            else:
                severity = "low"
            
            # Create alert
            alert = Alert(
                company_id=company_id,
                alert_type="score_change",
                severity=severity,
                title=f"Credit Score Change Alert",
                message=f"Credit score changed by {score_change:+.1f} points ({change_percentage:+.1f}%)",
                score_change=score_change,
                previous_score=previous_score,
                current_score=current_score,
                change_percentage=change_percentage,
                trigger_value=score_change,
                threshold_value=self.score_change_threshold,
                context_data={
                    'change_direction': 'increase' if score_change > 0 else 'decrease',
                    'change_magnitude': abs(score_change)
                }
            )
            
            self.db.add(alert)
            self.db.commit()
            
            logger.info(f"Created score change alert for company {company_id}: {score_change:+.1f} points")
            return alert
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating score change alert: {e}")
            return None
    
    def create_news_alert(self, company_id: int, news_event) -> Optional[Alert]:
        """Create alert for high-risk news events"""
        try:
            # Check if news event is high-risk
            if not self._is_high_risk_news(news_event):
                return None
            
            # Determine severity based on event type and sentiment
            severity = self._determine_news_severity(news_event)
            
            # Create alert
            alert = Alert(
                company_id=company_id,
                alert_type="news_event",
                severity=severity,
                title=f"High-Risk News Alert: {news_event.event_type.title()}",
                message=f"High-risk news detected: {news_event.headline[:100]}...",
                trigger_value=news_event.risk_score,
                threshold_value=0.7,
                context_data={
                    'event_type': news_event.event_type,
                    'sentiment_score': news_event.sentiment_score,
                    'risk_score': news_event.risk_score,
                    'keywords': news_event.keywords
                },
                related_events=[{
                    'headline': news_event.headline,
                    'url': news_event.url,
                    'published_at': news_event.published_at.isoformat()
                }]
            )
            
            self.db.add(alert)
            self.db.commit()
            
            logger.info(f"Created news alert for company {company_id}: {news_event.event_type}")
            return alert
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating news alert: {e}")
            return None
    
    def _is_high_risk_news(self, news_event) -> bool:
        """Check if news event is high-risk"""
        high_risk_events = ['default', 'legal', 'restructuring']
        high_risk_sentiment = news_event.sentiment_score < -0.5
        high_risk_score = news_event.risk_score > 0.7
        
        return (news_event.event_type in high_risk_events or 
                high_risk_sentiment or 
                high_risk_score)
    
    def _determine_news_severity(self, news_event) -> str:
        """Determine severity for news alert"""
        if news_event.event_type == 'default':
            return "critical"
        elif news_event.event_type in ['legal', 'restructuring']:
            return "high"
        elif news_event.sentiment_score < -0.7:
            return "high"
        elif news_event.sentiment_score < -0.3:
            return "medium"
        else:
            return "low"
    
    def _format_alert(self, alert: Alert) -> Dict[str, Any]:
        """Format alert for API response"""
        return {
            'id': alert.id,
            'ticker': alert.company.ticker,
            'company_name': alert.company.name,
            'alert_type': alert.alert_type,
            'severity': alert.severity,
            'title': alert.title,
            'message': alert.message,
            'score_change': alert.score_change,
            'previous_score': alert.previous_score,
            'current_score': alert.current_score,
            'change_percentage': alert.change_percentage,
            'is_read': alert.is_read,
            'is_acknowledged': alert.is_acknowledged,
            'acknowledged_by': alert.acknowledged_by,
            'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
            'context_data': alert.context_data,
            'related_events': alert.related_events,
            'created_at': alert.created_at.isoformat(),
            'expires_at': alert.expires_at.isoformat() if alert.expires_at else None
        }
    
    def cleanup_expired_alerts(self) -> int:
        """Clean up expired alerts"""
        try:
            expired_alerts = self.db.query(Alert).filter(
                Alert.expires_at < datetime.now()
            ).all()
            
            count = len(expired_alerts)
            for alert in expired_alerts:
                self.db.delete(alert)
            
            self.db.commit()
            
            if count > 0:
                logger.info(f"Cleaned up {count} expired alerts")
            
            return count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cleaning up expired alerts: {e}")
            return 0




