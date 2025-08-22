from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Company(Base):
    """Company model for storing company information"""
    
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    sector = Column(String(100))
    industry = Column(String(100))
    market_cap = Column(Integer)  # In millions
    description = Column(Text)
    website = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    financial_data = relationship("FinancialData", back_populates="company")
    news_events = relationship("NewsEvent", back_populates="company")
    credit_scores = relationship("CreditScore", back_populates="company")
    alerts = relationship("Alert", back_populates="company")
    
    def __repr__(self):
        return f"<Company(ticker='{self.ticker}', name='{self.name}')>"
