from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.database import get_db
from app.services.scoring_service import ScoringService
from app.schemas.scoring import CreditScoreResponse, ScoreExplanation

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/compute/{ticker}")
async def compute_credit_score(
    ticker: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Compute credit score for a company"""
    try:
        scoring_service = ScoringService(db)
        result = await scoring_service.compute_credit_score(ticker, background_tasks)
        return {
            "message": f"Credit score computation initiated for {ticker}",
            "ticker": ticker,
            "status": "processing"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error computing credit score for {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/score/{ticker}", response_model=CreditScoreResponse)
async def get_credit_score(
    ticker: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Get latest credit score for a company (auto-compute if not exists)"""
    try:
        scoring_service = ScoringService(db)
        score = scoring_service.get_latest_credit_score(ticker)
        
        if not score:
            # Try to compute the score immediately
            logger.info(f"No credit score found for {ticker}, attempting to compute...")
            try:
                # Check if we have the required data first
                has_financial_data = scoring_service._get_latest_financial_data(ticker) is not None
                has_news_data = scoring_service._get_latest_news_data(ticker) is not None
                
                if not has_financial_data:
                    raise HTTPException(
                        status_code=404, 
                        detail=f"No financial data available for {ticker}. Please fetch data first using POST /api/v1/data/fetch/{ticker}"
                    )
                
                # Compute score synchronously for immediate response
                await scoring_service._compute_score_background(ticker)
                
                # Try to get the score again
                score = scoring_service.get_latest_credit_score(ticker)
                
                if not score:
                    raise HTTPException(
                        status_code=500, 
                        detail=f"Failed to compute credit score for {ticker}. Please try again."
                    )
                    
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error computing score for {ticker}: {e}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"Error computing credit score for {ticker}: {str(e)}"
                )
        
        return score
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching credit score for {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/scores/{ticker}/history")
async def get_credit_score_history(
    ticker: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get credit score history for a company"""
    try:
        scoring_service = ScoringService(db)
        history = scoring_service.get_credit_score_history(ticker, days=days)
        if not history:
            raise HTTPException(status_code=404, detail="Credit score history not found")
        return history
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching credit score history for {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/explanation/{ticker}", response_model=ScoreExplanation)
async def get_score_explanation(
    ticker: str,
    db: Session = Depends(get_db)
):
    """Get detailed explanation for latest credit score"""
    try:
        scoring_service = ScoringService(db)
        explanation = scoring_service.get_score_explanation(ticker)
        if not explanation:
            raise HTTPException(status_code=404, detail="Score explanation not found")
        return explanation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching score explanation for {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/feature-importance/{ticker}")
async def get_feature_importance(
    ticker: str,
    db: Session = Depends(get_db)
):
    """Get feature importance breakdown for latest credit score"""
    try:
        scoring_service = ScoringService(db)
        importance = scoring_service.get_feature_importance(ticker)
        if not importance:
            raise HTTPException(status_code=404, detail="Feature importance not found")
        return importance
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching feature importance for {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/trends/{ticker}")
async def get_score_trends(
    ticker: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get credit score trends and analysis"""
    try:
        scoring_service = ScoringService(db)
        trends = scoring_service.get_score_trends(ticker, days=days)
        if not trends:
            raise HTTPException(status_code=404, detail="Score trends not found")
        return trends
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching score trends for {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/compute-all")
async def compute_all_credit_scores(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Compute credit scores for all active companies"""
    try:
        scoring_service = ScoringService(db)
        result = await scoring_service.compute_all_credit_scores(background_tasks)
        return {
            "message": "Credit score computation initiated for all companies",
            "companies_count": result["companies_count"],
            "status": "processing"
        }
    except Exception as e:
        logger.error(f"Error computing all credit scores: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/leaderboard")
async def get_credit_score_leaderboard(
    limit: int = Query(10, ge=1, le=100),
    sector: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get credit score leaderboard"""
    try:
        scoring_service = ScoringService(db)
        leaderboard = scoring_service.get_leaderboard(limit=limit, sector=sector)
        return leaderboard
    except Exception as e:
        logger.error(f"Error fetching credit score leaderboard: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")




