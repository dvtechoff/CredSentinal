from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CompanyBase(BaseModel):
    """Base company schema"""
    ticker: str = Field(..., min_length=1, max_length=10, description="Stock ticker symbol")
    name: str = Field(..., min_length=1, max_length=255, description="Company name")
    sector: Optional[str] = Field(None, max_length=100, description="Business sector")
    industry: Optional[str] = Field(None, max_length=100, description="Industry classification")
    market_cap: Optional[int] = Field(None, description="Market capitalization in millions")
    description: Optional[str] = Field(None, description="Company description")
    website: Optional[str] = Field(None, max_length=255, description="Company website")


class CompanyCreate(CompanyBase):
    """Schema for creating a new company"""
    pass


class CompanyUpdate(BaseModel):
    """Schema for updating company information"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    sector: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    market_cap: Optional[int] = Field(None)
    description: Optional[str] = Field(None)
    website: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = Field(None)


class CompanyResponse(CompanyBase):
    """Schema for company response"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CompanySummary(BaseModel):
    """Schema for company summary with latest data"""
    company: CompanyResponse
    latest_financial_data: Optional[dict] = None
    latest_credit_score: Optional[dict] = None
    latest_news: Optional[list] = None
    alerts_count: int = 0
    
    class Config:
        from_attributes = True




