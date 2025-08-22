from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.database import get_db
from app.services.news_service import NewsService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{ticker}")
async def get_news(
    ticker: str,
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(50, ge=1, le=100),
    sentiment_filter: Optional[str] = Query(None, regex="^(positive|negative|neutral)$"),
    db: Session = Depends(get_db)
):
    """Get news articles for a company"""
    try:
        news_service = NewsService(db)
        news = news_service.get_news(ticker, days=days, limit=limit, sentiment_filter=sentiment_filter)
        if not news:
            raise HTTPException(status_code=404, detail="News not found")
        return news
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching news for {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{ticker}/sentiment")
async def get_news_sentiment(
    ticker: str,
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """Get sentiment analysis summary for company news"""
    try:
        news_service = NewsService(db)
        sentiment = news_service.get_sentiment_summary(ticker, days=days)
        if not sentiment:
            raise HTTPException(status_code=404, detail="Sentiment data not found")
        return sentiment
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching sentiment for {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{ticker}/events")
async def get_news_events(
    ticker: str,
    days: int = Query(7, ge=1, le=30),
    event_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get classified news events for a company"""
    try:
        news_service = NewsService(db)
        events = news_service.get_news_events(ticker, days=days, event_type=event_type)
        if not events:
            raise HTTPException(status_code=404, detail="News events not found")
        return events
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching news events for {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/trending")
async def get_trending_news(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get trending news across all companies"""
    try:
        news_service = NewsService(db)
        trending = news_service.get_trending_news(limit=limit)
        return trending
    except Exception as e:
        logger.error(f"Error fetching trending news: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")




