from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class FinancialData(Base):
    """Financial data model for storing structured financial metrics"""
    
    __tablename__ = "financial_data"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    
    # Stock price data
    stock_price = Column(Float)
    volume = Column(Integer)
    market_cap = Column(Float)  # In millions
    
    # Financial ratios
    debt_to_equity = Column(Float)
    current_ratio = Column(Float)
    quick_ratio = Column(Float)
    return_on_equity = Column(Float)
    return_on_assets = Column(Float)
    
    # Earnings and revenue
    eps = Column(Float)
    revenue = Column(Float)  # In millions
    revenue_growth = Column(Float)  # Year over year
    net_income = Column(Float)  # In millions
    
    # Market indicators
    pe_ratio = Column(Float)
    pb_ratio = Column(Float)
    dividend_yield = Column(Float)
    
    # Volatility metrics
    price_volatility = Column(Float)  # 30-day volatility
    beta = Column(Float)
    
    # Additional metadata
    data_source = Column(String(50), default="yahoo_finance")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    company = relationship("Company", back_populates="financial_data")
    
    def __repr__(self):
        return f"<FinancialData(company_id={self.company_id}, date={self.date})>"




