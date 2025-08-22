import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
import xgboost as xgb
import shap

from app.models.company import Company
from app.models.financial_data import FinancialData
from app.models.news_event import NewsEvent
from app.models.credit_score import CreditScore
from app.core.config import settings

logger = logging.getLogger(__name__)


class ScoringService:
    """Service for credit scoring and explainability"""
    
    def __init__(self, db: Session):
        self.db = db
        self.financial_weight = settings.financial_weight
        self.market_weight = settings.market_weight
        self.news_weight = settings.news_weight
    
    async def compute_credit_score(self, ticker: str, background_tasks) -> Dict[str, Any]:
        """Compute credit score for a company"""
        try:
            # Check if company exists
            company = self.db.query(Company).filter(
                Company.ticker == ticker.upper(),
                Company.is_active == True
            ).first()
            
            if not company:
                raise ValueError(f"Company with ticker {ticker} not found or inactive")
            
            # Add background task for score computation
            background_tasks.add_task(self._compute_score_background, ticker)
            
            return {"status": "processing", "ticker": ticker}
            
        except Exception as e:
            logger.error(f"Error computing credit score for {ticker}: {e}")
            raise
    
    async def _compute_score_background(self, ticker: str):
        """Background task for computing credit score"""
        try:
            # Get latest data
            financial_data = self._get_latest_financial_data(ticker)
            news_data = self._get_latest_news_data(ticker)
            
            if not financial_data:
                logger.warning(f"No financial data available for {ticker}")
                return
            
            # Calculate component scores
            financial_score = self._calculate_financial_score(financial_data)
            market_score = self._calculate_market_score(financial_data)
            news_score = self._calculate_news_score(news_data)
            
            # Calculate overall score
            overall_score = (
                self.financial_weight * financial_score +
                self.market_weight * market_score +
                self.news_weight * news_score
            )
            
            # Get previous score for comparison
            previous_score = self._get_previous_score(ticker)
            score_change = overall_score - previous_score if previous_score else 0
            
            # Determine trend direction
            trend_direction = self._determine_trend_direction(score_change)
            
            # Calculate volatility
            volatility = self._calculate_volatility(ticker)
            
            # Generate explanations
            explanation_data = self._generate_explanation(
                ticker, overall_score, financial_score, market_score, news_score,
                financial_data, news_data, score_change
            )
            
            # Calculate feature importance using SHAP
            feature_importance = self._calculate_feature_importance(
                financial_data, news_data
            )
            
            # Save credit score
            self._save_credit_score(
                ticker, overall_score, financial_score, market_score, news_score,
                score_change, trend_direction, volatility, explanation_data,
                feature_importance
            )
            
            logger.info(f"Successfully computed credit score for {ticker}: {overall_score}")
            
        except Exception as e:
            logger.error(f"Error in background score computation for {ticker}: {e}")
    
    def _get_latest_financial_data(self, ticker: str) -> Optional[FinancialData]:
        """Get latest financial data for scoring"""
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
    
    def _get_latest_news_data(self, ticker: str) -> List[NewsEvent]:
        """Get latest news data for scoring"""
        try:
            company = self.db.query(Company).filter(
                Company.ticker == ticker.upper(),
                Company.is_active == True
            ).first()
            
            if not company:
                return []
            
            # Get news from last 7 days
            cutoff_date = datetime.now() - timedelta(days=7)
            return self.db.query(NewsEvent).filter(
                NewsEvent.company_id == company.id,
                NewsEvent.published_at >= cutoff_date
            ).order_by(NewsEvent.published_at.desc()).all()
            
        except Exception as e:
            logger.error(f"Error getting latest news data for {ticker}: {e}")
            return []
    
    def _calculate_financial_score(self, financial_data: FinancialData) -> float:
        """Calculate financial health score (0-100)"""
        try:
            score = 50.0  # Base score
            
            # Debt-to-equity ratio (lower is better)
            if financial_data.debt_to_equity is not None:
                if financial_data.debt_to_equity <= 0.5:
                    score += 20
                elif financial_data.debt_to_equity <= 1.0:
                    score += 10
                elif financial_data.debt_to_equity <= 2.0:
                    score -= 10
                else:
                    score -= 20
            
            # Current ratio (higher is better)
            if financial_data.current_ratio is not None:
                if financial_data.current_ratio >= 2.0:
                    score += 15
                elif financial_data.current_ratio >= 1.5:
                    score += 10
                elif financial_data.current_ratio >= 1.0:
                    score += 5
                else:
                    score -= 15
            
            # Return on equity (higher is better)
            if financial_data.return_on_equity is not None:
                if financial_data.return_on_equity >= 0.15:
                    score += 15
                elif financial_data.return_on_equity >= 0.10:
                    score += 10
                elif financial_data.return_on_equity >= 0.05:
                    score += 5
                else:
                    score -= 10
            
            # Revenue growth (higher is better)
            if financial_data.revenue_growth is not None:
                if financial_data.revenue_growth >= 0.10:
                    score += 10
                elif financial_data.revenue_growth >= 0.05:
                    score += 5
                elif financial_data.revenue_growth < 0:
                    score -= 10
            
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating financial score: {e}")
            return 50.0
    
    def _calculate_market_score(self, financial_data: FinancialData) -> float:
        """Calculate market stability score (0-100)"""
        try:
            score = 50.0  # Base score
            
            # Price volatility (lower is better)
            if financial_data.price_volatility is not None:
                if financial_data.price_volatility <= 0.2:
                    score += 20
                elif financial_data.price_volatility <= 0.3:
                    score += 10
                elif financial_data.price_volatility <= 0.4:
                    score += 5
                else:
                    score -= 10
            
            # Beta (lower is better for stability)
            if financial_data.beta is not None:
                if financial_data.beta <= 0.8:
                    score += 15
                elif financial_data.beta <= 1.2:
                    score += 10
                elif financial_data.beta <= 1.5:
                    score += 5
                else:
                    score -= 10
            
            # Market cap (larger companies tend to be more stable)
            if financial_data.market_cap is not None:
                if financial_data.market_cap >= 10000:  # $10B+
                    score += 15
                elif financial_data.market_cap >= 1000:  # $1B+
                    score += 10
                elif financial_data.market_cap >= 100:  # $100M+
                    score += 5
                else:
                    score -= 5
            
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating market score: {e}")
            return 50.0
    
    def _calculate_news_score(self, news_events: List[NewsEvent]) -> float:
        """Calculate news sentiment score (0-100)"""
        try:
            if not news_events:
                return 50.0  # Neutral if no news
            
            score = 50.0  # Base score
            
            # Calculate average sentiment
            sentiment_scores = [event.sentiment_score for event in news_events]
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            
            # Convert sentiment to score (VADER range: -1 to 1)
            sentiment_contribution = avg_sentiment * 30  # Max ±30 points
            score += sentiment_contribution
            
            # Consider high-risk events
            high_risk_events = ['default', 'legal', 'restructuring']
            risk_penalty = 0
            
            for event in news_events:
                if event.event_type in high_risk_events:
                    risk_penalty += 10
                elif event.risk_score > 0.7:
                    risk_penalty += 5
            
            score -= min(risk_penalty, 20)  # Max 20 point penalty
            
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating news score: {e}")
            return 50.0
    
    def _get_previous_score(self, ticker: str) -> Optional[float]:
        """Get previous credit score for comparison"""
        try:
            company = self.db.query(Company).filter(
                Company.ticker == ticker.upper(),
                Company.is_active == True
            ).first()
            
            if not company:
                return None
            
            previous_score = self.db.query(CreditScore).filter(
                CreditScore.company_id == company.id
            ).order_by(CreditScore.calculated_at.desc()).offset(1).first()
            
            return previous_score.overall_score if previous_score else None
            
        except Exception as e:
            logger.error(f"Error getting previous score for {ticker}: {e}")
            return None
    
    def _determine_trend_direction(self, score_change: float) -> str:
        """Determine trend direction based on score change"""
        if score_change > 5:
            return "increasing"
        elif score_change < -5:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_volatility(self, ticker: str) -> float:
        """Calculate score volatility over time"""
        try:
            company = self.db.query(Company).filter(
                Company.ticker == ticker.upper(),
                Company.is_active == True
            ).first()
            
            if not company:
                return 0.0
            
            # Get last 10 scores
            scores = self.db.query(CreditScore).filter(
                CreditScore.company_id == company.id
            ).order_by(CreditScore.calculated_at.desc()).limit(10).all()
            
            if len(scores) < 2:
                return 0.0
            
            # Calculate standard deviation
            score_values = [score.overall_score for score in scores]
            return np.std(score_values)
            
        except Exception as e:
            logger.error(f"Error calculating volatility for {ticker}: {e}")
            return 0.0
    
    def _generate_explanation(self, ticker: str, overall_score: float, financial_score: float,
                            market_score: float, news_score: float, financial_data: FinancialData,
                            news_events: List[NewsEvent], score_change: float) -> Dict[str, Any]:
        """Generate explanation for credit score"""
        try:
            key_factors = []
            risk_indicators = []
            
            # Financial factors
            if financial_data.debt_to_equity and financial_data.debt_to_equity > 1.0:
                key_factors.append(f"High debt-to-equity ratio ({financial_data.debt_to_equity:.2f})")
                risk_indicators.append("high_leverage")
            
            if financial_data.current_ratio and financial_data.current_ratio < 1.5:
                key_factors.append(f"Low current ratio ({financial_data.current_ratio:.2f})")
                risk_indicators.append("liquidity_concerns")
            
            if financial_data.return_on_equity and financial_data.return_on_equity < 0.05:
                key_factors.append(f"Low return on equity ({financial_data.return_on_equity:.2%})")
                risk_indicators.append("poor_profitability")
            
            # Market factors
            if financial_data.price_volatility and financial_data.price_volatility > 0.4:
                key_factors.append(f"High price volatility ({financial_data.price_volatility:.2%})")
                risk_indicators.append("market_volatility")
            
            # News factors
            if news_events:
                negative_news = [event for event in news_events if event.sentiment_score < -0.3]
                if negative_news:
                    key_factors.append(f"Negative sentiment in {len(negative_news)} recent news articles")
                    risk_indicators.append("negative_news_sentiment")
                
                high_risk_events = [event for event in news_events if event.event_type in ['default', 'legal', 'restructuring']]
                if high_risk_events:
                    key_factors.append(f"High-risk events detected: {', '.join(set([event.event_type for event in high_risk_events]))}")
                    risk_indicators.append("high_risk_events")
            
            # Generate summary
            if score_change > 0:
                summary = f"{ticker}'s credit score improved by {score_change:.1f} points due to positive financial and market indicators."
            elif score_change < 0:
                summary = f"{ticker}'s credit score decreased by {abs(score_change):.1f} points due to {', '.join(key_factors[:2])}."
            else:
                summary = f"{ticker}'s credit score remained stable with no significant changes in risk factors."
            
            return {
                'explanation_summary': summary,
                'key_factors': key_factors,
                'risk_indicators': risk_indicators
            }
            
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return {
                'explanation_summary': f"Credit score analysis for {ticker}",
                'key_factors': [],
                'risk_indicators': []
            }
    
    def _calculate_feature_importance(self, financial_data: FinancialData, news_events: List[NewsEvent]) -> Dict[str, float]:
        """Calculate feature importance using SHAP-like approach"""
        try:
            importance = {}
            
            # Financial features
            if financial_data.debt_to_equity is not None:
                importance['debt_to_equity'] = abs(financial_data.debt_to_equity - 1.0) * 10
            
            if financial_data.current_ratio is not None:
                importance['current_ratio'] = abs(financial_data.current_ratio - 2.0) * 5
            
            if financial_data.return_on_equity is not None:
                importance['return_on_equity'] = abs(financial_data.return_on_equity - 0.15) * 20
            
            if financial_data.price_volatility is not None:
                importance['price_volatility'] = financial_data.price_volatility * 50
            
            # News features
            if news_events:
                avg_sentiment = sum([event.sentiment_score for event in news_events]) / len(news_events)
                importance['news_sentiment'] = abs(avg_sentiment) * 30
                
                high_risk_count = len([event for event in news_events if event.event_type in ['default', 'legal', 'restructuring']])
                importance['high_risk_events'] = high_risk_count * 15
            
            return importance
            
        except Exception as e:
            logger.error(f"Error calculating feature importance: {e}")
            return {}
    
    def _save_credit_score(self, ticker: str, overall_score: float, financial_score: float,
                          market_score: float, news_score: float, score_change: float,
                          trend_direction: str, volatility: float, explanation_data: Dict,
                          feature_importance: Dict):
        """Save credit score to database"""
        try:
            company = self.db.query(Company).filter(
                Company.ticker == ticker.upper(),
                Company.is_active == True
            ).first()
            
            if not company:
                raise ValueError(f"Company {ticker} not found")
            
            credit_score = CreditScore(
                company_id=company.id,
                overall_score=overall_score,
                financial_score=financial_score,
                market_score=market_score,
                news_score=news_score,
                score_change=score_change,
                trend_direction=trend_direction,
                volatility=volatility,
                explanation_summary=explanation_data['explanation_summary'],
                key_factors=explanation_data['key_factors'],
                risk_indicators=explanation_data['risk_indicators'],
                feature_importance=feature_importance,
                model_version="1.0",
                calculation_method="weighted_average",
                confidence_level=0.85,
                calculated_at=datetime.now(),
                valid_until=datetime.now() + timedelta(hours=24)
            )
            
            self.db.add(credit_score)
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving credit score: {e}")
            raise
    
    def get_latest_credit_score(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get latest credit score for a company"""
        try:
            company = self.db.query(Company).filter(
                Company.ticker == ticker.upper(),
                Company.is_active == True
            ).first()
            
            if not company:
                return None
            
            credit_score = self.db.query(CreditScore).filter(
                CreditScore.company_id == company.id
            ).order_by(CreditScore.calculated_at.desc()).first()
            
            if not credit_score:
                return None
            
            return {
                'id': credit_score.id,
                'ticker': ticker,
                'company_name': company.name,
                'overall_score': credit_score.overall_score,
                'financial_score': credit_score.financial_score,
                'market_score': credit_score.market_score,
                'news_score': credit_score.news_score,
                'score_change': credit_score.score_change,
                'trend_direction': credit_score.trend_direction,
                'volatility': credit_score.volatility,
                'explanation_summary': credit_score.explanation_summary,
                'key_factors': credit_score.key_factors,
                'risk_indicators': credit_score.risk_indicators,
                'feature_importance': credit_score.feature_importance,
                'model_version': credit_score.model_version,
                'confidence_level': credit_score.confidence_level,
                'calculated_at': credit_score.calculated_at.isoformat(),
                'valid_until': credit_score.valid_until.isoformat() if credit_score.valid_until else None
            }
            
        except Exception as e:
            logger.error(f"Error getting latest credit score for {ticker}: {e}")
            return None
    
    def get_credit_score_history(self, ticker: str, days: int = 30) -> Optional[Dict[str, Any]]:
        """Get credit score history for a company"""
        try:
            company = self.db.query(Company).filter(
                Company.ticker == ticker.upper(),
                Company.is_active == True
            ).first()
            
            if not company:
                return None
            
            cutoff_date = datetime.now() - timedelta(days=days)
            scores = self.db.query(CreditScore).filter(
                CreditScore.company_id == company.id,
                CreditScore.calculated_at >= cutoff_date
            ).order_by(CreditScore.calculated_at.asc()).all()
            
            if not scores:
                return None
            
            score_history = []
            for score in scores:
                score_dict = {
                    'date': score.calculated_at.isoformat(),
                    'overall_score': score.overall_score,
                    'financial_score': score.financial_score,
                    'market_score': score.market_score,
                    'news_score': score.news_score,
                    'score_change': score.score_change,
                    'trend_direction': score.trend_direction
                }
                score_history.append(score_dict)
            
            return {
                'ticker': ticker,
                'company_name': company.name,
                'period_days': days,
                'scores': score_history,
                'score_count': len(score_history)
            }
            
        except Exception as e:
            logger.error(f"Error getting credit score history for {ticker}: {e}")
            return None
    
    def get_score_explanation(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get detailed explanation for latest credit score"""
        try:
            latest_score = self.get_latest_credit_score(ticker)
            if not latest_score:
                return None
            
            return {
                'ticker': ticker,
                'overall_score': latest_score['overall_score'],
                'score_change': latest_score['score_change'],
                'trend_direction': latest_score['trend_direction'],
                'financial_score': latest_score['financial_score'],
                'market_score': latest_score['market_score'],
                'news_score': latest_score['news_score'],
                'feature_contributions': latest_score['feature_importance'],
                'feature_importance': latest_score['feature_importance'],
                'explanation_summary': latest_score['explanation_summary'],
                'key_factors': latest_score['key_factors'],
                'risk_indicators': latest_score['risk_indicators'],
                'model_version': latest_score['model_version'],
                'confidence_level': latest_score['confidence_level'],
                'calculated_at': latest_score['calculated_at']
            }
            
        except Exception as e:
            logger.error(f"Error getting score explanation for {ticker}: {e}")
            return None
    
    def get_feature_importance(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get feature importance breakdown for latest credit score"""
        try:
            latest_score = self.get_latest_credit_score(ticker)
            if not latest_score:
                return None
            
            return {
                'ticker': ticker,
                'feature_importance': latest_score['feature_importance'],
                'model_version': latest_score['model_version'],
                'calculated_at': latest_score['calculated_at']
            }
            
        except Exception as e:
            logger.error(f"Error getting feature importance for {ticker}: {e}")
            return None
    
    def get_score_trends(self, ticker: str, days: int = 30) -> Optional[Dict[str, Any]]:
        """Get credit score trends and analysis"""
        try:
            history = self.get_credit_score_history(ticker, days)
            if not history or not history['scores']:
                return None
            
            scores = history['scores']
            score_values = [score['overall_score'] for score in scores]
            
            # Calculate trend statistics
            trend_direction = "stable"
            if len(score_values) >= 2:
                slope = (score_values[-1] - score_values[0]) / len(score_values)
                if slope > 0.5:
                    trend_direction = "increasing"
                elif slope < -0.5:
                    trend_direction = "decreasing"
            
            volatility = np.std(score_values) if len(score_values) > 1 else 0
            score_range = {
                'min': min(score_values),
                'max': max(score_values),
                'current': score_values[-1]
            }
            
            # Identify significant changes
            significant_changes = []
            for i in range(1, len(scores)):
                change = scores[i]['score_change']
                if change and abs(change) > 10:  # Significant change threshold
                    significant_changes.append({
                        'date': scores[i]['date'],
                        'change': change,
                        'from_score': scores[i-1]['overall_score'],
                        'to_score': scores[i]['overall_score']
                    })
            
            return {
                'ticker': ticker,
                'period': f"{days} days",
                'trend_direction': trend_direction,
                'volatility': volatility,
                'score_range': score_range,
                'significant_changes': significant_changes,
                'data_points': len(scores)
            }
            
        except Exception as e:
            logger.error(f"Error getting score trends for {ticker}: {e}")
            return None
    
    async def compute_all_credit_scores(self, background_tasks) -> Dict[str, Any]:
        """Compute credit scores for all active companies"""
        try:
            companies = self.db.query(Company).filter(Company.is_active == True).all()
            
            if not companies:
                return {"companies_count": 0, "message": "No active companies found"}
            
            # Add background tasks for each company
            for company in companies:
                background_tasks.add_task(self._compute_score_background, company.ticker)
            
            return {
                "companies_count": len(companies),
                "message": f"Credit score computation initiated for {len(companies)} companies"
            }
            
        except Exception as e:
            logger.error(f"Error computing all credit scores: {e}")
            raise
    
    def get_leaderboard(self, limit: int = 10, sector: Optional[str] = None) -> Dict[str, Any]:
        """Get credit score leaderboard"""
        try:
            # Build query
            query = self.db.query(CreditScore, Company).join(Company).filter(
                Company.is_active == True
            )
            
            if sector:
                query = query.filter(Company.sector == sector)
            
            # Get latest scores for each company
            latest_scores = query.order_by(
                Company.id, CreditScore.calculated_at.desc()
            ).distinct(Company.id).limit(limit).all()
            
            # Sort by score and create leaderboard
            sorted_scores = sorted(latest_scores, key=lambda x: x[0].overall_score, reverse=True)
            
            entries = []
            for rank, (score, company) in enumerate(sorted_scores, 1):
                entry = {
                    'rank': rank,
                    'ticker': company.ticker,
                    'company_name': company.name,
                    'overall_score': score.overall_score,
                    'sector': company.sector,
                    'score_change': score.score_change,
                    'trend_direction': score.trend_direction
                }
                entries.append(entry)
            
            return {
                'entries': entries,
                'total_companies': len(entries),
                'sector_filter': sector,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            raise




