import yfinance as yf
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
import time
from fredapi import Fred

from app.models.company import Company
from app.models.financial_data import FinancialData
from app.core.config import settings

logger = logging.getLogger(__name__)


class FinancialService:
    """Service for fetching and processing financial data"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def fetch_financial_data(self, ticker: str) -> Dict[str, Any]:
        """Fetch financial data from Yahoo Finance"""
        try:
            # Check if company exists
            company = self.db.query(Company).filter(
                Company.ticker == ticker.upper(),
                Company.is_active == True
            ).first()
            
            if not company:
                raise ValueError(f"Company with ticker {ticker} not found or inactive")
            
            # Fetch data from Yahoo Finance
            ticker_obj = yf.Ticker(ticker)
            
            # Get stock info
            info = ticker_obj.info
            
            # Get historical data
            hist = ticker_obj.history(period="1y")
            
            # Calculate financial metrics
            financial_data = self._process_financial_data(ticker, info, hist)
            
            # Save to database
            self._save_financial_data(company.id, financial_data)
            
            logger.info(f"Successfully fetched financial data for {ticker}")
            return {"status": "success", "ticker": ticker}
            
        except Exception as e:
            logger.error(f"Error fetching financial data for {ticker}: {e}")
            raise
    
    def _process_financial_data(self, ticker: str, info: Dict, hist: pd.DataFrame) -> Dict[str, Any]:
        """Process raw financial data into structured format"""
        try:
            # Extract basic info
            stock_price = info.get('currentPrice', hist['Close'].iloc[-1] if not hist.empty else None)
            market_cap = info.get('marketCap', 0) / 1e6  # Convert to millions
            volume = info.get('volume', hist['Volume'].iloc[-1] if not hist.empty else None)
            
            # Financial ratios
            debt_to_equity = info.get('debtToEquity', None)
            current_ratio = info.get('currentRatio', None)
            quick_ratio = info.get('quickRatio', None)
            return_on_equity = info.get('returnOnEquity', None)
            return_on_assets = info.get('returnOnAssets', None)
            
            # Earnings and revenue
            eps = info.get('trailingEps', None)
            revenue = info.get('totalRevenue', 0) / 1e6  # Convert to millions
            net_income = info.get('netIncomeToCommon', 0) / 1e6  # Convert to millions
            
            # Market indicators
            pe_ratio = info.get('trailingPE', None)
            pb_ratio = info.get('priceToBook', None)
            dividend_yield = info.get('dividendYield', None)
            
            # Calculate volatility (30-day)
            if not hist.empty and len(hist) >= 30:
                returns = hist['Close'].pct_change().dropna()
                volatility = returns.std() * np.sqrt(252)  # Annualized
                beta = info.get('beta', None)
            else:
                volatility = None
                beta = None
            
            # Calculate revenue growth (if available)
            revenue_growth = None
            if 'totalRevenue' in info and info.get('totalRevenue', 0) > 0:
                # This would need historical revenue data for proper calculation
                revenue_growth = 0.0  # Placeholder
            
            return {
                'stock_price': stock_price,
                'volume': volume,
                'market_cap': market_cap,
                'debt_to_equity': debt_to_equity,
                'current_ratio': current_ratio,
                'quick_ratio': quick_ratio,
                'return_on_equity': return_on_equity,
                'return_on_assets': return_on_assets,
                'eps': eps,
                'revenue': revenue,
                'revenue_growth': revenue_growth,
                'net_income': net_income,
                'pe_ratio': pe_ratio,
                'pb_ratio': pb_ratio,
                'dividend_yield': dividend_yield,
                'price_volatility': volatility,
                'beta': beta
            }
            
        except Exception as e:
            logger.error(f"Error processing financial data for {ticker}: {e}")
            raise
    
    def _save_financial_data(self, company_id: int, data: Dict[str, Any]):
        """Save financial data to database"""
        try:
            financial_data = FinancialData(
                company_id=company_id,
                date=datetime.now(),
                stock_price=data.get('stock_price'),
                volume=data.get('volume'),
                market_cap=data.get('market_cap'),
                debt_to_equity=data.get('debt_to_equity'),
                current_ratio=data.get('current_ratio'),
                quick_ratio=data.get('quick_ratio'),
                return_on_equity=data.get('return_on_equity'),
                return_on_assets=data.get('return_on_assets'),
                eps=data.get('eps'),
                revenue=data.get('revenue'),
                revenue_growth=data.get('revenue_growth'),
                net_income=data.get('net_income'),
                pe_ratio=data.get('pe_ratio'),
                pb_ratio=data.get('pb_ratio'),
                dividend_yield=data.get('dividend_yield'),
                price_volatility=data.get('price_volatility'),
                beta=data.get('beta'),
                data_source='yahoo_finance'
            )
            
            self.db.add(financial_data)
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving financial data: {e}")
            raise
    
    def get_financial_data(self, ticker: str, days: int = 30) -> Dict[str, Any]:
        """Get financial data for a company"""
        try:
            company = self.db.query(Company).filter(
                Company.ticker == ticker.upper(),
                Company.is_active == True
            ).first()
            
            if not company:
                return None
            
            # Get financial data for the specified period
            cutoff_date = datetime.now() - timedelta(days=days)
            financial_data = self.db.query(FinancialData).filter(
                FinancialData.company_id == company.id,
                FinancialData.date >= cutoff_date
            ).order_by(FinancialData.date.desc()).all()
            
            if not financial_data:
                return None
            
            # Convert to list of dictionaries
            data_list = []
            for data in financial_data:
                data_dict = {
                    'date': data.date.isoformat(),
                    'stock_price': data.stock_price,
                    'volume': data.volume,
                    'market_cap': data.market_cap,
                    'debt_to_equity': data.debt_to_equity,
                    'current_ratio': data.current_ratio,
                    'quick_ratio': data.quick_ratio,
                    'return_on_equity': data.return_on_equity,
                    'return_on_assets': data.return_on_assets,
                    'eps': data.eps,
                    'revenue': data.revenue,
                    'revenue_growth': data.revenue_growth,
                    'net_income': data.net_income,
                    'pe_ratio': data.pe_ratio,
                    'pb_ratio': data.pb_ratio,
                    'dividend_yield': data.dividend_yield,
                    'price_volatility': data.price_volatility,
                    'beta': data.beta
                }
                data_list.append(data_dict)
            
            return {
                'ticker': ticker,
                'company_name': company.name,
                'data_points': len(data_list),
                'latest_data': data_list[0] if data_list else None,
                'historical_data': data_list
            }
            
        except Exception as e:
            logger.error(f"Error getting financial data for {ticker}: {e}")
            raise
    
    def get_latest_financial_data(self, ticker: str) -> Optional[FinancialData]:
        """Get latest financial data for a company"""
        try:
            company = self.db.query(Company).filter(
                Company.ticker == ticker.upper(),
                Company.is_active == True
            ).first()
            
            if not company:
                return None
            
            return self.db.query(FinancialData).filter(
                FinancialData.company_id == company.id
            ).order_by(FinancialData.date.desc()).first()
            
        except Exception as e:
            logger.error(f"Error getting latest financial data for {ticker}: {e}")
            return None
    
    def get_data_quality_metrics(self, ticker: str) -> Dict[str, Any]:
        """Get data quality metrics for financial data"""
        try:
            company = self.db.query(Company).filter(
                Company.ticker == ticker.upper(),
                Company.is_active == True
            ).first()
            
            if not company:
                return None
            
            # Get recent data
            cutoff_date = datetime.now() - timedelta(days=30)
            recent_data = self.db.query(FinancialData).filter(
                FinancialData.company_id == company.id,
                FinancialData.date >= cutoff_date
            ).all()
            
            if not recent_data:
                return {
                    'completeness': 0.0,
                    'freshness': 0.0,
                    'data_points': 0
                }
            
            # Calculate completeness (percentage of non-null values)
            total_fields = len(recent_data) * 15  # Number of financial fields
            non_null_fields = sum(
                sum(1 for field in [
                    data.stock_price, data.volume, data.market_cap,
                    data.debt_to_equity, data.current_ratio, data.quick_ratio,
                    data.return_on_equity, data.return_on_assets, data.eps,
                    data.revenue, data.revenue_growth, data.net_income,
                    data.pe_ratio, data.pb_ratio, data.dividend_yield
                ] if field is not None)
                for data in recent_data
            )
            completeness = non_null_fields / total_fields if total_fields > 0 else 0.0
            
            # Calculate freshness (how recent the data is)
            latest_data = max(recent_data, key=lambda x: x.date)
            age_hours = (datetime.now() - latest_data.date).total_seconds() / 3600
            freshness = max(0, 1 - (age_hours / 24))  # 24 hours = 0 freshness
            
            return {
                'completeness': completeness,
                'freshness': freshness,
                'data_points': len(recent_data),
                'latest_update': latest_data.date.isoformat(),
                'age_hours': age_hours
            }
            
        except Exception as e:
            logger.error(f"Error getting data quality metrics for {ticker}: {e}")
            return None



