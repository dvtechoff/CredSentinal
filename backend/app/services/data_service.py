from sqlalchemy.orm import Session
from typing import Dict, Any, List
import logging
from datetime import datetime, timedelta

from app.models.company import Company
from app.services.financial_service import FinancialService
from app.services.news_service import NewsService
from app.core.config import settings

logger = logging.getLogger(__name__)


class DataService:
    """Main data service for orchestrating data ingestion"""
    
    def __init__(self, db: Session):
        self.db = db
        self.financial_service = FinancialService(db)
        self.news_service = NewsService(db)
    
    async def fetch_all_data(self, ticker: str, background_tasks) -> Dict[str, Any]:
        """Fetch all data for a company (financial + news)"""
        try:
            # Check if company exists
            company = self.db.query(Company).filter(
                Company.ticker == ticker.upper(),
                Company.is_active == True
            ).first()
            
            if not company:
                raise ValueError(f"Company with ticker {ticker} not found or inactive")
            
            # Add background tasks for data fetching
            background_tasks.add_task(self.financial_service.fetch_financial_data, ticker)
            background_tasks.add_task(self.news_service.fetch_news_data, ticker)
            
            return {
                "financial_data": "fetching",
                "news_data": "fetching",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fetching all data for {ticker}: {e}")
            raise
    
    def get_data_status(self, ticker: str) -> Dict[str, Any]:
        """Get data freshness status for a company"""
        try:
            company = self.db.query(Company).filter(
                Company.ticker == ticker.upper(),
                Company.is_active == True
            ).first()
            
            if not company:
                return None
            
            # Get latest financial data
            latest_financial = self.financial_service.get_latest_financial_data(ticker)
            latest_news = self.news_service.get_latest_news(ticker)
            
            status = {
                "ticker": ticker,
                "company_name": company.name,
                "financial_data": {
                    "has_data": latest_financial is not None,
                    "last_updated": latest_financial.created_at if latest_financial else None,
                    "age_hours": None
                },
                "news_data": {
                    "has_data": latest_news is not None,
                    "last_updated": latest_news.created_at if latest_news else None,
                    "age_hours": None
                }
            }
            
            # Calculate age in hours
            if latest_financial:
                age = datetime.now() - latest_financial.created_at
                status["financial_data"]["age_hours"] = age.total_seconds() / 3600
            
            if latest_news:
                age = datetime.now() - latest_news.created_at
                status["news_data"]["age_hours"] = age.total_seconds() / 3600
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting data status for {ticker}: {e}")
            raise
    
    async def refresh_all_data(self, background_tasks) -> Dict[str, Any]:
        """Refresh data for all active companies"""
        try:
            # Get all active companies
            companies = self.db.query(Company).filter(Company.is_active == True).all()
            
            if not companies:
                return {"companies_count": 0, "message": "No active companies found"}
            
            # Add background tasks for each company
            for company in companies:
                background_tasks.add_task(self.financial_service.fetch_financial_data, company.ticker)
                background_tasks.add_task(self.news_service.fetch_news_data, company.ticker)
            
            return {
                "companies_count": len(companies),
                "message": f"Data refresh initiated for {len(companies)} companies",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error refreshing all data: {e}")
            raise
    
    def get_data_quality_metrics(self, ticker: str) -> Dict[str, Any]:
        """Get data quality metrics for a company"""
        try:
            company = self.db.query(Company).filter(
                Company.ticker == ticker.upper(),
                Company.is_active == True
            ).first()
            
            if not company:
                return None
            
            # Get data quality metrics
            financial_metrics = self.financial_service.get_data_quality_metrics(ticker)
            news_metrics = self.news_service.get_data_quality_metrics(ticker)
            
            return {
                "ticker": ticker,
                "company_name": company.name,
                "financial_data": financial_metrics,
                "news_data": news_metrics,
                "overall_quality_score": self._calculate_quality_score(financial_metrics, news_metrics)
            }
            
        except Exception as e:
            logger.error(f"Error getting data quality metrics for {ticker}: {e}")
            raise
    
    def _calculate_quality_score(self, financial_metrics: Dict, news_metrics: Dict) -> float:
        """Calculate overall data quality score"""
        try:
            score = 0.0
            count = 0
            
            # Financial data quality
            if financial_metrics:
                if financial_metrics.get("completeness", 0) > 0:
                    score += financial_metrics["completeness"] * 0.6  # 60% weight
                    count += 1
                if financial_metrics.get("freshness", 0) > 0:
                    score += financial_metrics["freshness"] * 0.4  # 40% weight
                    count += 1
            
            # News data quality
            if news_metrics:
                if news_metrics.get("completeness", 0) > 0:
                    score += news_metrics["completeness"] * 0.5  # 50% weight
                    count += 1
                if news_metrics.get("freshness", 0) > 0:
                    score += news_metrics["freshness"] * 0.5  # 50% weight
                    count += 1
            
            return score / count if count > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return 0.0




