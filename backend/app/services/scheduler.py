from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timedelta
from typing import List

from app.core.database import SessionLocal
from app.services.data_service import DataService
from app.services.scoring_service import ScoringService
from app.services.alert_service import AlertService
from app.models.company import Company
from app.core.config import settings
from app.models.financial_data import FinancialData
from app.models.news_event import NewsEvent
from app.models.credit_score import CreditScore

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler()


def start_scheduler():
    """Start the scheduler with all configured jobs"""
    try:
        if not scheduler.running:
            # Data refresh job - every 30 minutes
            scheduler.add_job(
                refresh_all_data_job,
                CronTrigger(minute="*/30"),
                id="data_refresh",
                name="Refresh all company data",
                replace_existing=True
            )
            
            # Credit score computation job - every hour
            scheduler.add_job(
                compute_all_scores_job,
                CronTrigger(minute=0),  # Every hour at minute 0
                id="score_computation",
                name="Compute all credit scores",
                replace_existing=True
            )
            
            # Alert cleanup job - every 6 hours
            scheduler.add_job(
                cleanup_alerts_job,
                CronTrigger(hour="*/6"),
                id="alert_cleanup",
                name="Clean up expired alerts",
                replace_existing=True
            )
            
            # Daily maintenance job - at 2 AM
            scheduler.add_job(
                daily_maintenance_job,
                CronTrigger(hour=2, minute=0),
                id="daily_maintenance",
                name="Daily maintenance tasks",
                replace_existing=True
            )
            
            scheduler.start()
            logger.info("Scheduler started successfully")
            
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        raise


def stop_scheduler():
    """Stop the scheduler"""
    try:
        if scheduler.running:
            scheduler.shutdown()
            logger.info("Scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")


async def refresh_all_data_job():
    """Background job to refresh data for all companies"""
    logger.info("Starting data refresh job")
    
    try:
        db = SessionLocal()
        data_service = DataService(db)
        
        # Get all active companies
        companies = db.query(Company).filter(Company.is_active == True).all()
        
        if not companies:
            logger.info("No active companies found for data refresh")
            return
        
        logger.info(f"Refreshing data for {len(companies)} companies")
        
        # Refresh data for each company
        for company in companies:
            try:
                # Refresh financial data
                await data_service.financial_service.fetch_financial_data(company.ticker)
                
                # Refresh news data
                await data_service.news_service.fetch_news_data(company.ticker)
                
                logger.info(f"Refreshed data for {company.ticker}")
                
            except Exception as e:
                logger.error(f"Error refreshing data for {company.ticker}: {e}")
                continue
        
        logger.info("Data refresh job completed")
        
    except Exception as e:
        logger.error(f"Error in data refresh job: {e}")
    finally:
        db.close()


async def compute_all_scores_job():
    """Background job to compute credit scores for all companies"""
    logger.info("Starting credit score computation job")
    
    try:
        db = SessionLocal()
        scoring_service = ScoringService(db)
        
        # Get all active companies
        companies = db.query(Company).filter(Company.is_active == True).all()
        
        if not companies:
            logger.info("No active companies found for score computation")
            return
        
        logger.info(f"Computing scores for {len(companies)} companies")
        
        # Compute scores for each company
        for company in companies:
            try:
                await scoring_service._compute_score_background(company.ticker)
                logger.info(f"Computed score for {company.ticker}")
                
            except Exception as e:
                logger.error(f"Error computing score for {company.ticker}: {e}")
                continue
        
        logger.info("Credit score computation job completed")
        
    except Exception as e:
        logger.error(f"Error in credit score computation job: {e}")
    finally:
        db.close()


async def cleanup_alerts_job():
    """Background job to clean up expired alerts"""
    logger.info("Starting alert cleanup job")
    
    try:
        db = SessionLocal()
        alert_service = AlertService(db)
        
        # Clean up expired alerts
        cleaned_count = alert_service.cleanup_expired_alerts()
        
        logger.info(f"Alert cleanup job completed: {cleaned_count} alerts cleaned")
        
    except Exception as e:
        logger.error(f"Error in alert cleanup job: {e}")
    finally:
        db.close()


async def daily_maintenance_job():
    """Daily maintenance tasks"""
    logger.info("Starting daily maintenance job")
    
    try:
        db = SessionLocal()
        
        # Clean up old data (keep last 90 days)
        cutoff_date = datetime.now() - timedelta(days=90)
        
        # Clean up old financial data
        old_financial = db.query(FinancialData).filter(
            FinancialData.date < cutoff_date
        ).delete()
        
        # Clean up old news events
        old_news = db.query(NewsEvent).filter(
            NewsEvent.published_at < cutoff_date
        ).delete()
        
        # Clean up old credit scores (keep last 30 days)
        score_cutoff = datetime.now() - timedelta(days=30)
        old_scores = db.query(CreditScore).filter(
            CreditScore.calculated_at < score_cutoff
        ).delete()
        
        db.commit()
        
        logger.info(f"Daily maintenance completed: {old_financial} financial records, "
                   f"{old_news} news events, {old_scores} credit scores cleaned")
        
    except Exception as e:
        logger.error(f"Error in daily maintenance job: {e}")
        db.rollback()
    finally:
        db.close()


def add_company_to_scheduler(ticker: str):
    """Add a specific company to the data refresh schedule"""
    try:
        # Add immediate data refresh job
        scheduler.add_job(
            refresh_company_data_job,
            'date',
            args=[ticker],
            id=f"refresh_{ticker}",
            name=f"Refresh data for {ticker}",
            replace_existing=True
        )
        
        logger.info(f"Added {ticker} to scheduler")
        
    except Exception as e:
        logger.error(f"Error adding {ticker} to scheduler: {e}")


async def refresh_company_data_job(ticker: str):
    """Background job to refresh data for a specific company"""
    logger.info(f"Starting data refresh for {ticker}")
    
    try:
        db = SessionLocal()
        data_service = DataService(db)
        
        # Refresh financial data
        await data_service.financial_service.fetch_financial_data(ticker)
        
        # Refresh news data
        await data_service.news_service.fetch_news_data(ticker)
        
        # Compute credit score
        scoring_service = ScoringService(db)
        await scoring_service._compute_score_background(ticker)
        
        logger.info(f"Completed data refresh for {ticker}")
        
    except Exception as e:
        logger.error(f"Error refreshing data for {ticker}: {e}")
    finally:
        db.close()


def get_scheduler_status() -> dict:
    """Get scheduler status and job information"""
    try:
        jobs = []
        for job in scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        
        return {
            'running': scheduler.running,
            'job_count': len(jobs),
            'jobs': jobs
        }
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        return {'error': str(e)}


def pause_scheduler():
    """Pause the scheduler"""
    try:
        if scheduler.running:
            scheduler.pause()
            logger.info("Scheduler paused")
    except Exception as e:
        logger.error(f"Error pausing scheduler: {e}")


def resume_scheduler():
    """Resume the scheduler"""
    try:
        if scheduler.running:
            scheduler.resume()
            logger.info("Scheduler resumed")
    except Exception as e:
        logger.error(f"Error resuming scheduler: {e}")




