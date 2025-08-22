from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class NewsEvent(Base):
    """News event model for storing news headlines with sentiment analysis"""
    
    __tablename__ = "news_events"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # News content
    headline = Column(Text, nullable=False)
    summary = Column(Text)
    content = Column(Text)
    url = Column(String(500))
    source = Column(String(100))
    published_at = Column(DateTime)
    
    # Sentiment analysis
    sentiment_score = Column(Float)  # VADER compound score (-1 to 1)
    sentiment_label = Column(String(20))  # positive, negative, neutral
    positive_score = Column(Float)
    negative_score = Column(Float)
    neutral_score = Column(Float)
    
    # Event classification
    event_type = Column(String(50))  # default, merger, restructuring, etc.
    event_confidence = Column(Float)
    keywords = Column(JSON)  # List of detected keywords
    
    # Risk indicators
    risk_score = Column(Float)  # Calculated risk impact
    risk_factors = Column(JSON)  # List of risk factors
    
    # Metadata
    data_source = Column(String(50), default="newsapi")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    company = relationship("Company", back_populates="news_events")
    
    def __repr__(self):
        return f"<NewsEvent(company_id={self.company_id}, headline='{self.headline[:50]}...')>"




