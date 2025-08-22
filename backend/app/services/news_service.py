import requests
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
import json
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re

from app.models.company import Company
from app.models.news_event import NewsEvent
from app.core.config import settings

logger = logging.getLogger(__name__)


class NewsService:
    """Service for fetching and processing news data"""
    
    def __init__(self, db: Session):
        self.db = db
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self.news_api_key = settings.news_api_key
        
        # Event classification keywords
        self.event_keywords = {
            'default': ['default', 'bankruptcy', 'insolvency', 'liquidation', 'chapter 11'],
            'merger': ['merger', 'acquisition', 'takeover', 'buyout', 'consolidation'],
            'restructuring': ['restructuring', 'reorganization', 'layoffs', 'cost cutting'],
            'earnings': ['earnings', 'profit', 'loss', 'quarterly results', 'financial results'],
            'debt': ['debt', 'bond', 'credit rating', 'downgrade', 'upgrade'],
            'legal': ['lawsuit', 'litigation', 'regulatory', 'investigation', 'fine'],
            'management': ['ceo', 'executive', 'leadership', 'resignation', 'appointment']
        }
    
    async def fetch_news_data(self, ticker: str) -> Dict[str, Any]:
        """Fetch news data from NewsAPI"""
        try:
            # Check if company exists
            company = self.db.query(Company).filter(
                Company.ticker == ticker.upper(),
                Company.is_active == True
            ).first()
            
            if not company:
                raise ValueError(f"Company with ticker {ticker} not found or inactive")
            
            if not self.news_api_key:
                logger.warning("NewsAPI key not configured, using mock data")
                return await self._fetch_mock_news_data(ticker, company.id)
            
            # Fetch news from NewsAPI
            news_data = self._fetch_from_newsapi(ticker, company.name)
            
            # Process and save news articles
            processed_count = 0
            for article in news_data.get('articles', []):
                try:
                    # Analyze sentiment
                    sentiment_data = self._analyze_sentiment(article['title'] + ' ' + (article.get('description', '')))
                    
                    # Classify events
                    event_data = self._classify_events(article['title'] + ' ' + (article.get('description', '')))
                    
                    # Save to database
                    self._save_news_event(company.id, article, sentiment_data, event_data)
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing news article for {ticker}: {e}")
                    continue
            
            logger.info(f"Successfully processed {processed_count} news articles for {ticker}")
            return {"status": "success", "ticker": ticker, "articles_processed": processed_count}
            
        except Exception as e:
            logger.error(f"Error fetching news data for {ticker}: {e}")
            raise
    
    def _fetch_from_newsapi(self, ticker: str, company_name: str) -> Dict[str, Any]:
        """Fetch news from NewsAPI"""
        try:
            # Search for both ticker and company name
            query = f'"{ticker}" OR "{company_name}"'
            
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': query,
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': 50,
                'apiKey': self.news_api_key
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching from NewsAPI: {e}")
            raise
    
    async def _fetch_mock_news_data(self, ticker: str, company_id: int) -> Dict[str, Any]:
        """Fetch mock news data for testing"""
        try:
            mock_articles = [
                {
                    'title': f'{ticker} Reports Strong Quarterly Earnings',
                    'description': f'{ticker} exceeded analyst expectations with strong quarterly results.',
                    'url': f'https://example.com/news/{ticker}-earnings',
                    'source': {'name': 'Financial Times'},
                    'publishedAt': datetime.now().isoformat()
                },
                {
                    'title': f'{ticker} Announces New Product Launch',
                    'description': f'{ticker} is launching a new innovative product line.',
                    'url': f'https://example.com/news/{ticker}-product',
                    'source': {'name': 'Reuters'},
                    'publishedAt': (datetime.now() - timedelta(hours=2)).isoformat()
                },
                {
                    'title': f'{ticker} Faces Regulatory Challenges',
                    'description': f'{ticker} is dealing with new regulatory requirements.',
                    'url': f'https://example.com/news/{ticker}-regulatory',
                    'source': {'name': 'Bloomberg'},
                    'publishedAt': (datetime.now() - timedelta(hours=4)).isoformat()
                }
            ]
            
            processed_count = 0
            for article in mock_articles:
                try:
                    sentiment_data = self._analyze_sentiment(article['title'] + ' ' + article['description'])
                    event_data = self._classify_events(article['title'] + ' ' + article['description'])
                    self._save_news_event(company_id, article, sentiment_data, event_data)
                    processed_count += 1
                except Exception as e:
                    logger.error(f"Error processing mock article: {e}")
                    continue
            
            return {"status": "success", "ticker": ticker, "articles_processed": processed_count}
            
        except Exception as e:
            logger.error(f"Error fetching mock news data: {e}")
            raise
    
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using VADER"""
        try:
            # Clean text
            clean_text = re.sub(r'[^\w\s]', '', text.lower())
            
            # Get sentiment scores
            scores = self.sentiment_analyzer.polarity_scores(clean_text)
            
            # Determine sentiment label
            compound = scores['compound']
            if compound >= 0.05:
                sentiment_label = 'positive'
            elif compound <= -0.05:
                sentiment_label = 'negative'
            else:
                sentiment_label = 'neutral'
            
            return {
                'sentiment_score': compound,
                'sentiment_label': sentiment_label,
                'positive_score': scores['pos'],
                'negative_score': scores['neg'],
                'neutral_score': scores['neu']
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral',
                'positive_score': 0.0,
                'negative_score': 0.0,
                'neutral_score': 1.0
            }
    
    def _classify_events(self, text: str) -> Dict[str, Any]:
        """Classify news events based on keywords"""
        try:
            text_lower = text.lower()
            detected_events = []
            keywords_found = []
            
            for event_type, keywords in self.event_keywords.items():
                for keyword in keywords:
                    if keyword in text_lower:
                        detected_events.append(event_type)
                        keywords_found.append(keyword)
                        break  # Only count each event type once
            
            # Calculate confidence based on keyword matches
            confidence = min(1.0, len(keywords_found) * 0.3)
            
            return {
                'event_type': detected_events[0] if detected_events else None,
                'event_confidence': confidence,
                'keywords': keywords_found
            }
            
        except Exception as e:
            logger.error(f"Error classifying events: {e}")
            return {
                'event_type': None,
                'event_confidence': 0.0,
                'keywords': []
            }
    
    def _save_news_event(self, company_id: int, article: Dict, sentiment_data: Dict, event_data: Dict):
        """Save news event to database"""
        try:
            # Calculate risk score based on sentiment and events
            risk_score = self._calculate_risk_score(sentiment_data, event_data)
            risk_factors = self._identify_risk_factors(sentiment_data, event_data)
            
            news_event = NewsEvent(
                company_id=company_id,
                headline=article['title'],
                summary=article.get('description'),
                content=article.get('content'),
                url=article.get('url'),
                source=article.get('source', {}).get('name'),
                published_at=datetime.fromisoformat(article['publishedAt'].replace('Z', '+00:00')),
                sentiment_score=sentiment_data['sentiment_score'],
                sentiment_label=sentiment_data['sentiment_label'],
                positive_score=sentiment_data['positive_score'],
                negative_score=sentiment_data['negative_score'],
                neutral_score=sentiment_data['neutral_score'],
                event_type=event_data['event_type'],
                event_confidence=event_data['event_confidence'],
                keywords=event_data['keywords'],
                risk_score=risk_score,
                risk_factors=risk_factors,
                data_source='newsapi'
            )
            
            self.db.add(news_event)
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving news event: {e}")
            raise
    
    def _calculate_risk_score(self, sentiment_data: Dict, event_data: Dict) -> float:
        """Calculate risk score based on sentiment and events"""
        try:
            risk_score = 0.0
            
            # Sentiment contribution (negative sentiment increases risk)
            sentiment_score = sentiment_data['sentiment_score']
            if sentiment_score < -0.3:
                risk_score += 0.4
            elif sentiment_score < 0:
                risk_score += 0.2
            
            # Event contribution
            high_risk_events = ['default', 'legal', 'restructuring']
            medium_risk_events = ['debt', 'management']
            
            if event_data['event_type'] in high_risk_events:
                risk_score += 0.4
            elif event_data['event_type'] in medium_risk_events:
                risk_score += 0.2
            
            return min(1.0, risk_score)
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return 0.0
    
    def _identify_risk_factors(self, sentiment_data: Dict, event_data: Dict) -> List[str]:
        """Identify risk factors from sentiment and events"""
        try:
            risk_factors = []
            
            # Sentiment-based risk factors
            if sentiment_data['sentiment_score'] < -0.3:
                risk_factors.append('negative_sentiment')
            elif sentiment_data['sentiment_score'] < 0:
                risk_factors.append('neutral_to_negative_sentiment')
            
            # Event-based risk factors
            if event_data['event_type']:
                risk_factors.append(f"{event_data['event_type']}_event")
            
            return risk_factors
            
        except Exception as e:
            logger.error(f"Error identifying risk factors: {e}")
            return []
    
    def get_news_data(self, ticker: str, days: int = 7, limit: int = 50) -> Dict[str, Any]:
        """Get news data for a company"""
        try:
            company = self.db.query(Company).filter(
                Company.ticker == ticker.upper(),
                Company.is_active == True
            ).first()
            
            if not company:
                return None
            
            # Get news for the specified period
            cutoff_date = datetime.now() - timedelta(days=days)
            news_events = self.db.query(NewsEvent).filter(
                NewsEvent.company_id == company.id,
                NewsEvent.published_at >= cutoff_date
            ).order_by(NewsEvent.published_at.desc()).limit(limit).all()
            
            if not news_events:
                return None
            
            # Convert to list of dictionaries
            news_list = []
            for event in news_events:
                news_dict = {
                    'id': event.id,
                    'headline': event.headline,
                    'summary': event.summary,
                    'url': event.url,
                    'source': event.source,
                    'published_at': event.published_at.isoformat(),
                    'sentiment_score': event.sentiment_score,
                    'sentiment_label': event.sentiment_label,
                    'event_type': event.event_type,
                    'risk_score': event.risk_score,
                    'risk_factors': event.risk_factors
                }
                news_list.append(news_dict)
            
            return {
                'ticker': ticker,
                'company_name': company.name,
                'articles_count': len(news_list),
                'latest_news': news_list
            }
            
        except Exception as e:
            logger.error(f"Error getting news data for {ticker}: {e}")
            raise
    
    def get_latest_news(self, ticker: str) -> Optional[NewsEvent]:
        """Get latest news for a company"""
        try:
            company = self.db.query(Company).filter(
                Company.ticker == ticker.upper(),
                Company.is_active == True
            ).first()
            
            if not company:
                return None
            
            return self.db.query(NewsEvent).filter(
                NewsEvent.company_id == company.id
            ).order_by(NewsEvent.published_at.desc()).first()
            
        except Exception as e:
            logger.error(f"Error getting latest news for {ticker}: {e}")
            return None
    
    def get_sentiment_summary(self, ticker: str, days: int = 7) -> Dict[str, Any]:
        """Get sentiment analysis summary for company news"""
        try:
            company = self.db.query(Company).filter(
                Company.ticker == ticker.upper(),
                Company.is_active == True
            ).first()
            
            if not company:
                return None
            
            # Get news for the specified period
            cutoff_date = datetime.now() - timedelta(days=days)
            news_events = self.db.query(NewsEvent).filter(
                NewsEvent.company_id == company.id,
                NewsEvent.published_at >= cutoff_date
            ).all()
            
            if not news_events:
                return None
            
            # Calculate sentiment statistics
            sentiment_scores = [event.sentiment_score for event in news_events]
            sentiment_labels = [event.sentiment_label for event in news_events]
            
            positive_count = sentiment_labels.count('positive')
            negative_count = sentiment_labels.count('negative')
            neutral_count = sentiment_labels.count('neutral')
            
            return {
                'ticker': ticker,
                'company_name': company.name,
                'period_days': days,
                'total_articles': len(news_events),
                'average_sentiment': sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0,
                'sentiment_distribution': {
                    'positive': positive_count,
                    'negative': negative_count,
                    'neutral': neutral_count
                },
                'sentiment_percentages': {
                    'positive': positive_count / len(news_events) * 100 if news_events else 0,
                    'negative': negative_count / len(news_events) * 100 if news_events else 0,
                    'neutral': neutral_count / len(news_events) * 100 if news_events else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting sentiment summary for {ticker}: {e}")
            raise
    
    def get_news_events(self, ticker: str, days: int = 7, event_type: Optional[str] = None) -> Dict[str, Any]:
        """Get classified news events for a company"""
        try:
            company = self.db.query(Company).filter(
                Company.ticker == ticker.upper(),
                Company.is_active == True
            ).first()
            
            if not company:
                return None
            
            # Build query
            query = self.db.query(NewsEvent).filter(
                NewsEvent.company_id == company.id,
                NewsEvent.published_at >= datetime.now() - timedelta(days=days)
            )
            
            if event_type:
                query = query.filter(NewsEvent.event_type == event_type)
            
            news_events = query.order_by(NewsEvent.published_at.desc()).all()
            
            if not news_events:
                return None
            
            # Group by event type
            events_by_type = {}
            for event in news_events:
                event_type = event.event_type or 'uncategorized'
                if event_type not in events_by_type:
                    events_by_type[event_type] = []
                
                events_by_type[event_type].append({
                    'id': event.id,
                    'headline': event.headline,
                    'published_at': event.published_at.isoformat(),
                    'sentiment_score': event.sentiment_score,
                    'risk_score': event.risk_score
                })
            
            return {
                'ticker': ticker,
                'company_name': company.name,
                'period_days': days,
                'events_by_type': events_by_type,
                'total_events': len(news_events)
            }
            
        except Exception as e:
            logger.error(f"Error getting news events for {ticker}: {e}")
            raise
    
    def get_trending_news(self, limit: int = 20) -> Dict[str, Any]:
        """Get trending news across all companies"""
        try:
            # Get recent news with high risk scores or negative sentiment
            cutoff_date = datetime.now() - timedelta(days=1)
            trending_news = self.db.query(NewsEvent).filter(
                NewsEvent.published_at >= cutoff_date,
                (NewsEvent.risk_score > 0.5) | (NewsEvent.sentiment_score < -0.3)
            ).order_by(NewsEvent.risk_score.desc(), NewsEvent.published_at.desc()).limit(limit).all()
            
            news_list = []
            for event in trending_news:
                news_dict = {
                    'ticker': event.company.ticker,
                    'company_name': event.company.name,
                    'headline': event.headline,
                    'published_at': event.published_at.isoformat(),
                    'sentiment_score': event.sentiment_score,
                    'event_type': event.event_type,
                    'risk_score': event.risk_score
                }
                news_list.append(news_dict)
            
            return {
                'trending_news': news_list,
                'total_articles': len(news_list),
                'period_hours': 24
            }
            
        except Exception as e:
            logger.error(f"Error getting trending news: {e}")
            raise
    
    def get_data_quality_metrics(self, ticker: str) -> Dict[str, Any]:
        """Get data quality metrics for news data"""
        try:
            company = self.db.query(Company).filter(
                Company.ticker == ticker.upper(),
                Company.is_active == True
            ).first()
            
            if not company:
                return None
            
            # Get recent news
            cutoff_date = datetime.now() - timedelta(days=7)
            recent_news = self.db.query(NewsEvent).filter(
                NewsEvent.company_id == company.id,
                NewsEvent.published_at >= cutoff_date
            ).all()
            
            if not recent_news:
                return {
                    'completeness': 0.0,
                    'freshness': 0.0,
                    'articles_count': 0
                }
            
            # Calculate completeness (percentage of articles with full data)
            total_fields = len(recent_news) * 8  # Number of news fields
            non_null_fields = sum(
                sum(1 for field in [
                    event.headline, event.sentiment_score, event.sentiment_label,
                    event.event_type, event.risk_score, event.source,
                    event.published_at, event.url
                ] if field is not None)
                for event in recent_news
            )
            completeness = non_null_fields / total_fields if total_fields > 0 else 0.0
            
            # Calculate freshness (how recent the news is)
            latest_news = max(recent_news, key=lambda x: x.published_at)
            age_hours = (datetime.now() - latest_news.published_at).total_seconds() / 3600
            freshness = max(0, 1 - (age_hours / 24))  # 24 hours = 0 freshness
            
            return {
                'completeness': completeness,
                'freshness': freshness,
                'articles_count': len(recent_news),
                'latest_update': latest_news.published_at.isoformat(),
                'age_hours': age_hours
            }
            
        except Exception as e:
            logger.error(f"Error getting data quality metrics for {ticker}: {e}")
            return None




