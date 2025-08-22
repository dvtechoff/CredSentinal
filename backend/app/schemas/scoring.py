from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class CreditScoreBase(BaseModel):
    """Base credit score schema"""
    overall_score: float = Field(..., ge=0, le=100, description="Overall credit score (0-100)")
    financial_score: Optional[float] = Field(None, ge=0, le=100)
    market_score: Optional[float] = Field(None, ge=0, le=100)
    news_score: Optional[float] = Field(None, ge=0, le=100)


class CreditScoreResponse(CreditScoreBase):
    """Schema for credit score response"""
    id: int
    company_id: int
    score_breakdown: Optional[Dict[str, Any]] = None
    feature_importance: Optional[Dict[str, float]] = None
    score_change: Optional[float] = None
    trend_direction: Optional[str] = None
    volatility: Optional[float] = None
    explanation_summary: Optional[str] = None
    key_factors: Optional[List[str]] = None
    risk_indicators: Optional[List[str]] = None
    model_version: str = "1.0"
    calculation_method: str = "weighted_average"
    confidence_level: Optional[float] = None
    calculated_at: datetime
    valid_until: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ScoreExplanation(BaseModel):
    """Schema for credit score explanation"""
    ticker: str
    overall_score: float
    score_change: Optional[float] = None
    trend_direction: Optional[str] = None
    
    # Component scores
    financial_score: Optional[float] = None
    market_score: Optional[float] = None
    news_score: Optional[float] = None
    
    # Feature contributions
    feature_contributions: Dict[str, float] = {}
    feature_importance: Dict[str, float] = {}
    
    # Explanations
    explanation_summary: str
    key_factors: List[str] = []
    risk_indicators: List[str] = []
    
    # Model metadata
    model_version: str = "1.0"
    confidence_level: Optional[float] = None
    calculated_at: datetime
    
    class Config:
        from_attributes = True


class ScoreHistory(BaseModel):
    """Schema for credit score history"""
    ticker: str
    scores: List[CreditScoreResponse]
    trend_analysis: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class ScoreTrends(BaseModel):
    """Schema for credit score trends"""
    ticker: str
    period: str
    trend_direction: str
    volatility: float
    score_range: Dict[str, float]
    significant_changes: List[Dict[str, Any]] = []
    
    class Config:
        from_attributes = True


class LeaderboardEntry(BaseModel):
    """Schema for leaderboard entry"""
    rank: int
    ticker: str
    company_name: str
    overall_score: float
    sector: Optional[str] = None
    score_change: Optional[float] = None
    trend_direction: Optional[str] = None
    
    class Config:
        from_attributes = True


class Leaderboard(BaseModel):
    """Schema for credit score leaderboard"""
    entries: List[LeaderboardEntry]
    total_companies: int
    sector_filter: Optional[str] = None
    generated_at: datetime
    
    class Config:
        from_attributes = True




