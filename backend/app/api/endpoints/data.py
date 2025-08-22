from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.database import get_db
from app.services.data_service import DataService
from app.services.financial_service import FinancialService
from app.services.news_service import NewsService
from app.services.company_service import CompanyService
from app.schemas.company import CompanyCreate

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/fetch/{ticker}")
async def fetch_company_data(
    ticker: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Fetch latest data for a company (financial + news)"""
    try:
        # First, check if company exists, if not create it
        company_service = CompanyService(db)
        company = company_service.get_company_by_ticker(ticker)
        
        if not company:
            # Create the company automatically
            company_data = CompanyCreate(
                ticker=ticker.upper(),
                name=f"{ticker.upper()} Corporation",  # Default name
                sector="Technology",  # Default sector
                industry="Software",  # Default industry
                description=f"Automatically created company for {ticker.upper()}"
            )
            company = company_service.create_company(company_data)
            logger.info(f"Auto-created company for ticker {ticker}")
        
        # Now fetch the data
        data_service = DataService(db)
        result = await data_service.fetch_all_data(ticker, background_tasks)
        return {
            "message": f"Data fetch initiated for {ticker}",
            "ticker": ticker,
            "company_created": company.created_at if hasattr(company, 'created_at') else None,
            "status": "processing",
            "tasks": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/fetch-sync/{ticker}")
async def fetch_company_data_sync(
    ticker: str,
    db: Session = Depends(get_db)
):
    """Fetch latest data for a company synchronously (immediate processing)"""
    try:
        # First, check if company exists, if not create it
        company_service = CompanyService(db)
        company = company_service.get_company_by_ticker(ticker)
        
        if not company:
            # Create the company automatically
            company_data = CompanyCreate(
                ticker=ticker.upper(),
                name=f"{ticker.upper()} Corporation",  # Default name
                sector="Technology",  # Default sector
                industry="Software",  # Default industry
                description=f"Automatically created company for {ticker.upper()}"
            )
            company = company_service.create_company(company_data)
            logger.info(f"Auto-created company for ticker {ticker}")
        
        # Fetch data synchronously
        financial_service = FinancialService(db)
        news_service = NewsService(db)
        
        # Fetch financial data
        financial_result = await financial_service.fetch_financial_data(ticker)
        
        # Fetch news data
        news_result = await news_service.fetch_news_data(ticker)
        
        return {
            "message": f"Data fetch completed for {ticker}",
            "ticker": ticker,
            "company_created": company.created_at if hasattr(company, 'created_at') else None,
            "status": "completed",
            "financial_data": financial_result,
            "news_data": news_result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/financial/{ticker}")
async def get_financial_data(
    ticker: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get financial data for a company"""
    try:
        financial_service = FinancialService(db)
        data = financial_service.get_financial_data(ticker, days=days)
        if not data:
            raise HTTPException(status_code=404, detail="Financial data not found")
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching financial data for {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/financial/{ticker}/refresh")
async def refresh_financial_data(
    ticker: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Refresh financial data for a company"""
    try:
        financial_service = FinancialService(db)
        result = await financial_service.refresh_financial_data(ticker, background_tasks)
        return {
            "message": f"Financial data refresh initiated for {ticker}",
            "ticker": ticker,
            "status": "processing"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error refreshing financial data for {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/news/{ticker}")
async def get_news_data(
    ticker: str,
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get news data for a company"""
    try:
        news_service = NewsService(db)
        data = news_service.get_news_data(ticker, days=days, limit=limit)
        if not data:
            raise HTTPException(status_code=404, detail="News data not found")
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching news data for {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/news/{ticker}/refresh")
async def refresh_news_data(
    ticker: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Refresh news data for a company"""
    try:
        news_service = NewsService(db)
        result = await news_service.refresh_news_data(ticker, background_tasks)
        return {
            "message": f"News data refresh initiated for {ticker}",
            "ticker": ticker,
            "status": "processing"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error refreshing news data for {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status/{ticker}")
async def get_data_status(ticker: str, db: Session = Depends(get_db)):
    """Get data freshness status for a company"""
    try:
        data_service = DataService(db)
        status = data_service.get_data_status(ticker)
        if not status:
            raise HTTPException(status_code=404, detail="Company not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting data status for {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/refresh-all")
async def refresh_all_data(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Refresh data for all active companies"""
    try:
        data_service = DataService(db)
        result = await data_service.refresh_all_data(background_tasks)
        return {
            "message": "Data refresh initiated for all companies",
            "companies_count": result["companies_count"],
            "status": "processing"
        }
    except Exception as e:
        logger.error(f"Error refreshing all data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")




