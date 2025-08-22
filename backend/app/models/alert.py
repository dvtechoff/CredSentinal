from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Alert(Base):
    """Alert model for storing system alerts and notifications"""
    
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # Alert details
    alert_type = Column(String(50), nullable=False)  # score_change, news_event, etc.
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # Score change details (if applicable)
    score_change = Column(Float)
    previous_score = Column(Float)
    current_score = Column(Float)
    change_percentage = Column(Float)
    
    # Trigger conditions
    trigger_value = Column(Float)  # Value that triggered the alert
    threshold_value = Column(Float)  # Threshold that was exceeded
    
    # Alert metadata
    is_read = Column(Boolean, default=False)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(100))
    acknowledged_at = Column(DateTime)
    
    # Additional context
    context_data = Column(JSON)  # Additional data for the alert
    related_events = Column(JSON)  # Related news events or data points
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime)  # When alert expires
    
    # Relationships
    company = relationship("Company", back_populates="alerts")
    
    def __repr__(self):
        return f"<Alert(company_id={self.company_id}, type='{self.alert_type}', severity='{self.severity}')>"




