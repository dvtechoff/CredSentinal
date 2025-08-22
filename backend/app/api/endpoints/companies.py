from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.database import get_db
from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate
from app.services.company_service import CompanyService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=List[CompanyResponse])
async def get_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Get list of companies"""
    try:
        service = CompanyService(db)
        companies = service.get_companies(skip=skip, limit=limit, active_only=active_only)
        return companies
    except Exception as e:
        logger.error(f"Error fetching companies: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{ticker}", response_model=CompanyResponse)
async def get_company(ticker: str, db: Session = Depends(get_db)):
    """Get company by ticker symbol"""
    try:
        service = CompanyService(db)
        company = service.get_company_by_ticker(ticker)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        return company
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching company {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=CompanyResponse)
async def create_company(
    company: CompanyCreate,
    db: Session = Depends(get_db)
):
    """Create a new company"""
    try:
        service = CompanyService(db)
        return service.create_company(company)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating company: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{ticker}", response_model=CompanyResponse)
async def update_company(
    ticker: str,
    company_update: CompanyUpdate,
    db: Session = Depends(get_db)
):
    """Update company information"""
    try:
        service = CompanyService(db)
        company = service.update_company(ticker, company_update)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        return company
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating company {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{ticker}")
async def delete_company(ticker: str, db: Session = Depends(get_db)):
    """Delete a company (soft delete)"""
    try:
        service = CompanyService(db)
        success = service.delete_company(ticker)
        if not success:
            raise HTTPException(status_code=404, detail="Company not found")
        return {"message": f"Company {ticker} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting company {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{ticker}/summary")
async def get_company_summary(ticker: str, db: Session = Depends(get_db)):
    """Get company summary with latest data"""
    try:
        service = CompanyService(db)
        summary = service.get_company_summary(ticker)
        if not summary:
            raise HTTPException(status_code=404, detail="Company not found")
        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching company summary for {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")




