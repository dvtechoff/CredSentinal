from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from app.models.company import Company
from app.models.financial_data import FinancialData
from app.models.credit_score import CreditScore
from app.models.news_event import NewsEvent
from app.models.alert import Alert
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse, CompanySummary

logger = logging.getLogger(__name__)


class CompanyService:
    """Service for managing company information"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_companies(self, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[CompanyResponse]:
        """Get list of companies"""
        try:
            query = self.db.query(Company)
            
            if active_only:
                query = query.filter(Company.is_active == True)
            
            companies = query.offset(skip).limit(limit).all()
            
            return [CompanyResponse.from_orm(company) for company in companies]
            
        except Exception as e:
            logger.error(f"Error getting companies: {e}")
            raise
    
    def get_company_by_ticker(self, ticker: str) -> Optional[CompanyResponse]:
        """Get company by ticker symbol"""
        try:
            company = self.db.query(Company).filter(
                Company.ticker == ticker.upper(),
                Company.is_active == True
            ).first()
            
            return CompanyResponse.from_orm(company) if company else None
            
        except Exception as e:
            logger.error(f"Error getting company by ticker {ticker}: {e}")
            raise
    
    def create_company(self, company_data: CompanyCreate) -> CompanyResponse:
        """Create a new company"""
        try:
            # Check if company already exists
            existing_company = self.db.query(Company).filter(
                Company.ticker == company_data.ticker.upper()
            ).first()
            
            if existing_company:
                raise ValueError(f"Company with ticker {company_data.ticker} already exists")
            
            # Create new company
            company = Company(
                ticker=company_data.ticker.upper(),
                name=company_data.name,
                sector=company_data.sector,
                industry=company_data.industry,
                market_cap=company_data.market_cap,
                description=company_data.description,
                website=company_data.website,
                is_active=True
            )
            
            self.db.add(company)
            self.db.commit()
            self.db.refresh(company)
            
            logger.info(f"Created new company: {company.ticker}")
            return CompanyResponse.from_orm(company)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating company: {e}")
            raise
    
    def update_company(self, ticker: str, company_update: CompanyUpdate) -> Optional[CompanyResponse]:
        """Update company information"""
        try:
            company = self.db.query(Company).filter(
                Company.ticker == ticker.upper(),
                Company.is_active == True
            ).first()
            
            if not company:
                return None
            
            # Update fields
            update_data = company_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(company, field, value)
            
            company.updated_at = datetime.now()
            
            self.db.commit()
            self.db.refresh(company)
            
            logger.info(f"Updated company: {company.ticker}")
            return CompanyResponse.from_orm(company)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating company {ticker}: {e}")
            raise
    
    def delete_company(self, ticker: str) -> bool:
        """Delete a company (soft delete)"""
        try:
            company = self.db.query(Company).filter(
                Company.ticker == ticker.upper(),
                Company.is_active == True
            ).first()
            
            if not company:
                return False
            
            # Soft delete
            company.is_active = False
            company.updated_at = datetime.now()
            
            self.db.commit()
            
            logger.info(f"Deleted company: {company.ticker}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting company {ticker}: {e}")
            raise
    
    def get_company_summary(self, ticker: str) -> Optional[CompanySummary]:
        """Get company summary with latest data"""
        try:
            company = self.db.query(Company).filter(
                Company.ticker == ticker.upper(),
                Company.is_active == True
            ).first()
            
            if not company:
                return None
            
            # Get latest financial data
            latest_financial = self.db.query(FinancialData).filter(
                FinancialData.company_id == company.id
            ).order_by(FinancialData.date.desc()).first()
            
            # Get latest credit score
            latest_score = self.db.query(CreditScore).filter(
                CreditScore.company_id == company.id
            ).order_by(CreditScore.calculated_at.desc()).first()
            
            # Get latest news
            latest_news = self.db.query(NewsEvent).filter(
                NewsEvent.company_id == company.id
            ).order_by(NewsEvent.published_at.desc()).limit(5).all()
            
            # Get alerts count
            alerts_count = self.db.query(Alert).filter(
                Alert.company_id == company.id,
                Alert.is_read == False
            ).count()
            
            # Convert to summary format
            summary = CompanySummary(
                company=CompanyResponse.from_orm(company),
                latest_financial_data=self._format_financial_data(latest_financial) if latest_financial else None,
                latest_credit_score=self._format_credit_score(latest_score) if latest_score else None,
                latest_news=self._format_news_data(latest_news) if latest_news else None,
                alerts_count=alerts_count
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting company summary for {ticker}: {e}")
            raise
    
    def _format_financial_data(self, financial_data: FinancialData) -> Dict[str, Any]:
        """Format financial data for summary"""
        return {
            'date': financial_data.date.isoformat(),
            'stock_price': financial_data.stock_price,
            'market_cap': financial_data.market_cap,
            'debt_to_equity': financial_data.debt_to_equity,
            'current_ratio': financial_data.current_ratio,
            'return_on_equity': financial_data.return_on_equity,
            'revenue': financial_data.revenue,
            'eps': financial_data.eps
        }
    
    def _format_credit_score(self, credit_score: CreditScore) -> Dict[str, Any]:
        """Format credit score for summary"""
        return {
            'overall_score': credit_score.overall_score,
            'financial_score': credit_score.financial_score,
            'market_score': credit_score.market_score,
            'news_score': credit_score.news_score,
            'trend_direction': credit_score.trend_direction,
            'calculated_at': credit_score.calculated_at.isoformat()
        }
    
    def _format_news_data(self, news_events: List[NewsEvent]) -> List[Dict[str, Any]]:
        """Format news data for summary"""
        return [
            {
                'headline': event.headline,
                'sentiment_score': event.sentiment_score,
                'sentiment_label': event.sentiment_label,
                'event_type': event.event_type,
                'published_at': event.published_at.isoformat()
            }
            for event in news_events
        ]
    
    def search_companies(self, query: str, limit: int = 10) -> List[CompanyResponse]:
        """Search companies by name or ticker"""
        try:
            companies = self.db.query(Company).filter(
                Company.is_active == True,
                (Company.name.ilike(f"%{query}%")) | (Company.ticker.ilike(f"%{query}%"))
            ).limit(limit).all()
            
            return [CompanyResponse.from_orm(company) for company in companies]
            
        except Exception as e:
            logger.error(f"Error searching companies: {e}")
            raise
    
    def get_companies_by_sector(self, sector: str, limit: int = 50) -> List[CompanyResponse]:
        """Get companies by sector"""
        try:
            companies = self.db.query(Company).filter(
                Company.sector == sector,
                Company.is_active == True
            ).limit(limit).all()
            
            return [CompanyResponse.from_orm(company) for company in companies]
            
        except Exception as e:
            logger.error(f"Error getting companies by sector {sector}: {e}")
            raise
    
    def get_company_statistics(self) -> Dict[str, Any]:
        """Get company statistics"""
        try:
            total_companies = self.db.query(Company).filter(Company.is_active == True).count()
            
            # Count by sector
            sector_counts = self.db.query(Company.sector, self.db.func.count(Company.id)).filter(
                Company.is_active == True,
                Company.sector.isnot(None)
            ).group_by(Company.sector).all()
            
            # Count by industry
            industry_counts = self.db.query(Company.industry, self.db.func.count(Company.id)).filter(
                Company.is_active == True,
                Company.industry.isnot(None)
            ).group_by(Company.industry).limit(10).all()
            
            return {
                'total_companies': total_companies,
                'sector_distribution': dict(sector_counts),
                'top_industries': dict(industry_counts)
            }
            
        except Exception as e:
            logger.error(f"Error getting company statistics: {e}")
            raise
