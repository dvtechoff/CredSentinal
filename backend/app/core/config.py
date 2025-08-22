from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    app_name: str = "News-Driven Credit Risk Monitor"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./credit_monitor.db")
    
    # API Keys
    # Yahoo Finance: No API key required (uses yfinance library)
    alpha_vantage_api_key: Optional[str] = os.getenv("ALPHA_VANTAGE_API_KEY")
    news_api_key: Optional[str] = os.getenv("NEWS_API_KEY")
    fred_api_key: Optional[str] = os.getenv("FRED_API_KEY")
    
    # Data Ingestion Settings
    data_refresh_interval: int = int(os.getenv("DATA_REFRESH_INTERVAL", "1800"))  # 30 minutes
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    retry_delay: int = int(os.getenv("RETRY_DELAY", "5"))
    
    # Scoring Model Weights
    financial_weight: float = float(os.getenv("FINANCIAL_WEIGHT", "0.4"))
    market_weight: float = float(os.getenv("MARKET_WEIGHT", "0.3"))
    news_weight: float = float(os.getenv("NEWS_WEIGHT", "0.3"))
    
    # Alert Settings
    score_change_threshold: float = float(os.getenv("SCORE_CHANGE_THRESHOLD", "20.0"))
    alert_time_window: int = int(os.getenv("ALERT_TIME_WINDOW", "86400"))  # 24 hours
    
    # CORS Settings
    cors_origins: list = ["*"]  # Configure appropriately for production
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Create settings instance
settings = Settings()



