from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class CreditScore(Base):
    """Credit score model for storing computed credit scores with explanations"""
    
    __tablename__ = "credit_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # Score components
    overall_score = Column(Float, nullable=False)  # 0-100 scale
    financial_score = Column(Float)  # Financial health component
    market_score = Column(Float)  # Market stability component
    news_score = Column(Float)  # News sentiment component
    
    # Score breakdown
    score_breakdown = Column(JSON)  # Detailed feature contributions
    feature_importance = Column(JSON)  # SHAP feature importance
    
    # Trend indicators
    score_change = Column(Float)  # Change from previous score
    trend_direction = Column(String(20))  # increasing, decreasing, stable
    volatility = Column(Float)  # Score volatility over time
    
    # Explanations
    explanation_summary = Column(Text)  # Plain language explanation
    key_factors = Column(JSON)  # List of key factors affecting score
    risk_indicators = Column(JSON)  # List of risk indicators
    
    # Model metadata
    model_version = Column(String(20), default="1.0")
    calculation_method = Column(String(50), default="weighted_average")
    confidence_level = Column(Float)  # Model confidence (0-1)
    
    # Timestamps
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    valid_until = Column(DateTime)  # When score expires
    
    # Relationships
    company = relationship("Company", back_populates="credit_scores")
    
    def __repr__(self):
        return f"<CreditScore(company_id={self.company_id}, score={self.overall_score})>"




