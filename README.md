# 🏗️ News-Driven Credit Risk Monitor

A real-time explainable credit intelligence platform that uses structured financial data + unstructured news data to produce creditworthiness scores with explanations, displayed in an interactive web dashboard.

## 🎯 Project Overview

This system provides real-time creditworthiness scoring that reacts quickly to financial news and market data, with explainable reasons for each score update. Perfect for financial analysts, risk managers, and credit officers who need actionable insights.

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │  Data Ingestion │    │   Processing    │
│                 │    │                 │    │   & Scoring     │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │Yahoo Finance│ │───▶│ │   Scheduler │ │───▶│ │  Feature    │ │
│ │   API       │ │    │ │  (Cron/APS) │ │    │ │ Engineering │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │Alpha Vantage│ │───▶│ │   ETL       │ │───▶│ │  Scoring    │ │
│ │   API       │ │    │ │  Scripts    │ │    │ │  Engine     │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │  NewsAPI    │ │───▶│ │   Error     │ │───▶│ │Explainability│ │
│ │             │ │    │ │  Handling   │ │    │ │   Layer     │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Storage       │    │  Presentation   │
                       │   Layer         │    │   Layer         │
                       │                 │    │                 │
                       │ ┌─────────────┐ │    │ ┌─────────────┐ │
                       │ │  Database   │ │    │ │  Streamlit  │ │
                       │ │ (SQLite/    │ │    │ │  Dashboard  │ │
                       │ │  Postgres)  │ │    │ │             │ │
                       │ └─────────────┘ │    │ └─────────────┘ │
                       └─────────────────┘    └─────────────────┘
```

## 🛠️ Tech Stack

### Backend
- **FastAPI** - High-performance web framework for APIs
- **Pandas** - Data manipulation and analysis
- **Scikit-learn** - Machine learning algorithms
- **XGBoost** - Gradient boosting for structured scoring
- **SHAP** - Model explainability and feature importance
- **VADER** - Sentiment analysis for news headlines

### Frontend
- **Streamlit** - Rapid web app development for data science
- **Plotly** - Interactive charts and visualizations
- **Pandas** - Data processing for dashboard

### Database
- **SQLite** - Local development (lightweight)
- **PostgreSQL** - Production deployment (scalable)

### Deployment
- **Docker** - Containerization
- **Render/Railway/Heroku** - Cloud hosting platforms

## 🚀 Features

### Core Functionality
- **Real-time Data Ingestion**: Automated fetching from Yahoo Finance, Alpha Vantage, and NewsAPI
- **Credit Scoring Engine**: Weighted model combining financial, market, and news factors
- **Explainable AI**: SHAP values and plain-language explanations for score changes
- **News Sentiment Analysis**: VADER sentiment scoring for financial headlines
- **Event Classification**: Keyword detection for risk events (default, merger, restructuring)

### Dashboard Features
- **Credit Score Trends**: Historical score visualization
- **Feature Contributions**: SHAP-based feature importance breakdown
- **News Feed**: Latest headlines with sentiment analysis
- **Alert System**: Notifications for significant score changes (>20 points)
- **Company Filtering**: Search and filter by ticker symbols

## 📊 Scoring Model

The credit score is computed using a weighted formula:

```
Credit Score = 0.4 × Financial Index + 0.3 × Market Index + 0.3 × News Sentiment Index
```

### Components:
- **Financial Index (40%)**: Debt-to-equity ratio, revenue growth, EPS changes
- **Market Index (30%)**: Stock price volatility, recent returns, market cap trends
- **News Sentiment Index (30%)**: Sentiment scores from headlines, event classification

## 🏃‍♂️ Quick Start

### Prerequisites
- Python 3.8+
- Docker (for deployment)
- API keys for:
  - Alpha Vantage API
  - NewsAPI
  - FRED API
  - Yahoo Finance (no API key required)

### Local Development

1. **Clone and Setup**
```bash
git clone https://github.com/dvtechoff/CredSentinal
cd CredSentinal
pip install -r requirements.txt
```

2. **Environment Configuration**
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Run Backend**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

4. **Run Frontend**
```bash
cd frontend
streamlit run app.py
```

### Docker Deployment

#### Option 1: Development (Recommended for Hackathon)
```bash
# Quick start with SQLite (no external database needed)
docker-compose -f docker-compose.dev.yml up --build

# Or use the launcher script
./run-docker.sh  # Linux/Mac
# or
.\run-docker.ps1  # Windows PowerShell
```

#### Option 2: Production (Full Stack)
```bash
# Full deployment with PostgreSQL, Redis, and Nginx
docker-compose up --build
```

#### Option 3: Individual Services
```bash
# Backend only
docker-compose -f docker-compose.dev.yml up --build backend

# Frontend only  
docker-compose -f docker-compose.dev.yml up --build frontend
```

## 📁 Project Structure

```
CredTech/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Configuration and utilities
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   └── ml/             # Machine learning models
│   ├── requirements.txt
│   └── main.py
├── frontend/               # Streamlit dashboard
│   ├── app.py
│   ├── components/         # Dashboard components
│   └── requirements.txt
├── database/               # Database schemas and migrations
├── docker/                 # Docker configuration
├── docs/                   # Documentation
└── README.md
```

## 🔧 Configuration

### Environment Variables
```bash
# API Keys
ALPHA_VANTAGE_API_KEY=your_key
NEWS_API_KEY=your_key
FRED_API_KEY=your_key
# Yahoo Finance: No API key required (uses yfinance library)

# Database
DATABASE_URL=sqlite:///./credit_monitor.db

# Application
DEBUG=True
LOG_LEVEL=INFO
```

## 📈 Usage Examples

### API Endpoints

```python
# Fetch latest data
GET /api/v1/fetch-data/{ticker}

# Compute credit score
GET /api/v1/compute-score/{ticker}

# Get explanation
GET /api/v1/get-explanation/{ticker}

# Get news feed
GET /api/v1/get-news/{ticker}
```

### Dashboard Features
- View credit score trends over time
- Analyze feature contributions with SHAP values
- Monitor news sentiment and events
- Set up alerts for score changes

## 🎯 Hackathon Roadmap

### Day 1: MVP
- [x] FastAPI backend setup
- [x] Yahoo Finance + Alpha Vantage + NewsAPI + FRED integration
- [x] Basic credit scoring algorithm
- [x] Streamlit dashboard with scores and news

### Day 2: Enhancement
- [x] VADER sentiment analysis integration
- [x] SHAP explainability layer
- [x] Feature breakdown visualization
- [x] Trend analysis and alerts

### Day 3: Polish & Deploy
- [x] Docker containerization
- [x] Public deployment
- [x] UI/UX improvements
- [x] Documentation and demo

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Yahoo Finance for financial data (no API key required)
- Alpha Vantage for market indicators
- NewsAPI for news headlines
- FRED for economic indicators
- VADER for sentiment analysis
- SHAP for model explainability

---

**Built for CredTech Hackathon** 🚀



