import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
AUTO_REFRESH_INTERVAL = 300  # 5 minutes

# Page configuration
st.set_page_config(
    page_title="News-Driven Credit Risk Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .alert-high {
        background-color: #ffebee;
        border-left-color: #f44336;
    }
    .alert-medium {
        background-color: #fff3e0;
        border-left-color: #ff9800;
    }
    .alert-low {
        background-color: #e8f5e8;
        border-left-color: #4caf50;
    }
</style>
""", unsafe_allow_html=True)


class CreditRiskMonitor:
    """Main application class for the credit risk monitor dashboard"""
    
    def __init__(self):
        self.api_base_url = API_BASE_URL
        self.session = requests.Session()
    
    def api_request(self, endpoint: str, method: str = "GET", data: dict = None) -> Optional[dict]:
        """Make API request to backend"""
        try:
            url = f"{self.api_base_url}{endpoint}"
            
            if method == "GET":
                response = self.session.get(url, timeout=30)
            elif method == "POST":
                response = self.session.post(url, json=data, timeout=30)
            else:
                return None
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {e}")
            return None
    
    def get_companies(self) -> List[dict]:
        """Get list of companies"""
        return self.api_request("/api/v1/companies/") or []
    
    def get_company_data(self, ticker: str) -> Optional[dict]:
        """Get company data"""
        return self.api_request(f"/api/v1/companies/{ticker}")
    
    def get_credit_score(self, ticker: str) -> Optional[dict]:
        """Get credit score for company"""
        return self.api_request(f"/api/v1/scoring/score/{ticker}")
    
    def get_score_history(self, ticker: str, days: int = 30) -> Optional[dict]:
        """Get credit score history"""
        return self.api_request(f"/api/v1/scoring/scores/{ticker}/history?days={days}")
    
    def get_score_explanation(self, ticker: str) -> Optional[dict]:
        """Get score explanation"""
        return self.api_request(f"/api/v1/scoring/explanation/{ticker}")
    
    def get_financial_data(self, ticker: str, days: int = 30) -> Optional[dict]:
        """Get financial data"""
        return self.api_request(f"/api/v1/data/financial/{ticker}?days={days}")
    
    def get_news_data(self, ticker: str, days: int = 7) -> Optional[dict]:
        """Get news data"""
        return self.api_request(f"/api/v1/news/{ticker}?days={days}")
    
    def get_alerts(self, ticker: str = None, unread_only: bool = True) -> List[dict]:
        """Get alerts"""
        endpoint = "/api/v1/alerts/"
        if ticker:
            endpoint = f"/api/v1/alerts/{ticker}"
        if unread_only:
            endpoint += "?unread_only=true"
        return self.api_request(endpoint) or []
    
    def get_leaderboard(self, limit: int = 10) -> Optional[dict]:
        """Get credit score leaderboard"""
        return self.api_request(f"/api/v1/scoring/leaderboard?limit={limit}")
    
    def refresh_data(self, ticker: str) -> bool:
        """Refresh data for company"""
        response = self.api_request(f"/api/v1/data/fetch/{ticker}", method="POST")
        return response is not None
    
    def compute_score(self, ticker: str) -> bool:
        """Compute credit score for company"""
        response = self.api_request(f"/api/v1/scoring/compute/{ticker}", method="POST")
        return response is not None


def main():
    """Main application function"""
    st.markdown('<h1 class="main-header">📊 News-Driven Credit Risk Monitor</h1>', unsafe_allow_html=True)
    
    # Initialize app
    app = CreditRiskMonitor()
    
    # Sidebar
    with st.sidebar:
        st.header("Navigation")
        
        # Company selection
        companies = app.get_companies()
        company_options = {f"{c['ticker']} - {c['name']}": c['ticker'] for c in companies}
        
        if company_options:
            selected_company = st.selectbox(
                "Select Company",
                options=list(company_options.keys()),
                index=0
            )
            selected_ticker = company_options[selected_company]
        else:
            selected_ticker = st.text_input("Enter Ticker Symbol", value="AAPL").upper()
        
        # Actions
        st.header("Actions")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Refresh Data"):
                with st.spinner("Refreshing data..."):
                    if app.refresh_data(selected_ticker):
                        st.success("Data refresh initiated!")
                    else:
                        st.error("Failed to refresh data")
        
        with col2:
            if st.button("📊 Compute Score"):
                with st.spinner("Computing score..."):
                    if app.compute_score(selected_ticker):
                        st.success("Score computation initiated!")
                    else:
                        st.error("Failed to compute score")
        
        # Auto-refresh
        st.header("Settings")
        auto_refresh = st.checkbox("Auto-refresh (5 min)", value=True)
        
        if auto_refresh:
            time.sleep(1)  # Simple auto-refresh simulation
    
    # Main content
    if selected_ticker:
        display_company_dashboard(app, selected_ticker)
    else:
        st.warning("Please select a company or enter a ticker symbol")


def display_company_dashboard(app: CreditRiskMonitor, ticker: str):
    """Display company dashboard"""
    
    # Header with company info
    company_data = app.get_company_data(ticker)
    if company_data:
        st.header(f"📈 {company_data['name']} ({ticker})")
        st.caption(f"Sector: {company_data.get('sector', 'N/A')} | Industry: {company_data.get('industry', 'N/A')}")
    else:
        st.header(f"📈 {ticker}")
    
    # Main metrics
    credit_score = app.get_credit_score(ticker)
    
    if credit_score:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Overall Score",
                f"{credit_score['overall_score']:.1f}",
                f"{credit_score.get('score_change', 0):+.1f}"
            )
        
        with col2:
            st.metric(
                "Financial Score",
                f"{credit_score.get('financial_score', 0):.1f}"
            )
        
        with col3:
            st.metric(
                "Market Score",
                f"{credit_score.get('market_score', 0):.1f}"
            )
        
        with col4:
            st.metric(
                "News Score",
                f"{credit_score.get('news_score', 0):.1f}"
            )
    
    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview", "📈 Score History", "💰 Financial Data", "📰 News & Sentiment", "⚠️ Alerts"
    ])
    
    with tab1:
        display_overview_tab(app, ticker, credit_score)
    
    with tab2:
        display_score_history_tab(app, ticker)
    
    with tab3:
        display_financial_tab(app, ticker)
    
    with tab4:
        display_news_tab(app, ticker)
    
    with tab5:
        display_alerts_tab(app, ticker)


def display_overview_tab(app: CreditRiskMonitor, ticker: str, credit_score: Optional[dict]):
    """Display overview tab"""
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Score explanation
        if credit_score:
            st.subheader("📋 Score Explanation")
            
            explanation = app.get_score_explanation(ticker)
            if explanation:
                st.write(explanation.get('explanation_summary', 'No explanation available'))
                
                # Key factors
                key_factors = explanation.get('key_factors', [])
                if key_factors:
                    st.write("**Key Factors:**")
                    for factor in key_factors:
                        st.write(f"• {factor}")
                
                # Risk indicators
                risk_indicators = explanation.get('risk_indicators', [])
                if risk_indicators:
                    st.write("**Risk Indicators:**")
                    for indicator in risk_indicators:
                        st.write(f"• {indicator}")
        
        # Feature importance
        if credit_score and credit_score.get('feature_importance'):
            st.subheader("🎯 Feature Importance")
            
            importance_data = credit_score['feature_importance']
            if importance_data:
                # Create bar chart
                features = list(importance_data.keys())
                values = list(importance_data.values())
                
                fig = px.bar(
                    x=features,
                    y=values,
                    title="Feature Importance",
                    labels={'x': 'Features', 'y': 'Importance Score'}
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Trend indicator
        if credit_score:
            st.subheader("📈 Trend")
            
            trend = credit_score.get('trend_direction', 'stable')
            trend_icon = {
                'increasing': '📈',
                'decreasing': '📉',
                'stable': '➡️'
            }.get(trend, '➡️')
            
            st.markdown(f"**{trend_icon} {trend.title()}**")
            
            # Volatility
            volatility = credit_score.get('volatility', 0)
            st.metric("Volatility", f"{volatility:.2f}")
        
        # Quick actions
        st.subheader("⚡ Quick Actions")
        
        if st.button("🔄 Refresh All Data", key="refresh_all"):
            with st.spinner("Refreshing all data..."):
                app.refresh_data(ticker)
                app.compute_score(ticker)
                st.success("Data refresh completed!")
        
        if st.button("📊 Recompute Score", key="recompute"):
            with st.spinner("Recomputing score..."):
                app.compute_score(ticker)
                st.success("Score recomputation completed!")


def display_score_history_tab(app: CreditRiskMonitor, ticker: str):
    """Display score history tab"""
    
    # Time period selector
    col1, col2 = st.columns([1, 3])
    with col1:
        days = st.selectbox("Time Period", [7, 30, 90, 180], index=1)
    
    # Get score history
    history = app.get_score_history(ticker, days)
    
    if history and history.get('scores'):
        scores = history['scores']
        
        # Create time series chart
        df = pd.DataFrame(scores)
        df['date'] = pd.to_datetime(df['date'])
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Overall Score', 'Component Scores'),
            vertical_spacing=0.1
        )
        
        # Overall score
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['overall_score'],
                mode='lines+markers',
                name='Overall Score',
                line=dict(color='#1f77b4', width=3)
            ),
            row=1, col=1
        )
        
        # Component scores
        if 'financial_score' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['date'],
                    y=df['financial_score'],
                    mode='lines',
                    name='Financial Score',
                    line=dict(color='#ff7f0e')
                ),
                row=2, col=1
            )
        
        if 'market_score' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['date'],
                    y=df['market_score'],
                    mode='lines',
                    name='Market Score',
                    line=dict(color='#2ca02c')
                ),
                row=2, col=1
            )
        
        if 'news_score' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['date'],
                    y=df['news_score'],
                    mode='lines',
                    name='News Score',
                    line=dict(color='#d62728')
                ),
                row=2, col=1
            )
        
        fig.update_layout(height=600, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
        
        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Average Score", f"{df['overall_score'].mean():.1f}")
        
        with col2:
            st.metric("Score Range", f"{df['overall_score'].max() - df['overall_score'].min():.1f}")
        
        with col3:
            st.metric("Data Points", len(df))
        
        with col4:
            latest_change = df['score_change'].iloc[-1] if 'score_change' in df.columns else 0
            st.metric("Latest Change", f"{latest_change:+.1f}")
    
    else:
        st.info("No score history available. Try refreshing the data.")


def display_financial_tab(app: CreditRiskMonitor, ticker: str):
    """Display financial data tab"""
    
    # Get financial data
    financial_data = app.get_financial_data(ticker, days=30)
    
    if financial_data and financial_data.get('historical_data'):
        data = financial_data['historical_data']
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        
        # Key metrics
        latest = df.iloc[0] if not df.empty else None
        
        if latest is not None:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if latest.get('stock_price'):
                    st.metric("Stock Price", f"${latest['stock_price']:.2f}")
            
            with col2:
                if latest.get('market_cap'):
                    st.metric("Market Cap", f"${latest['market_cap']:.0f}M")
            
            with col3:
                if latest.get('debt_to_equity'):
                    st.metric("Debt/Equity", f"{latest['debt_to_equity']:.2f}")
            
            with col4:
                if latest.get('current_ratio'):
                    st.metric("Current Ratio", f"{latest['current_ratio']:.2f}")
        
        # Financial ratios chart
        if not df.empty:
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Debt/Equity Ratio', 'Current Ratio', 'Return on Equity', 'Price Volatility'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # Debt/Equity
            if 'debt_to_equity' in df.columns:
                fig.add_trace(
                    go.Scatter(x=df['date'], y=df['debt_to_equity'], name='Debt/Equity'),
                    row=1, col=1
                )
            
            # Current Ratio
            if 'current_ratio' in df.columns:
                fig.add_trace(
                    go.Scatter(x=df['date'], y=df['current_ratio'], name='Current Ratio'),
                    row=1, col=2
                )
            
            # ROE
            if 'return_on_equity' in df.columns:
                fig.add_trace(
                    go.Scatter(x=df['date'], y=df['return_on_equity'], name='ROE'),
                    row=2, col=1
                )
            
            # Volatility
            if 'price_volatility' in df.columns:
                fig.add_trace(
                    go.Scatter(x=df['date'], y=df['price_volatility'], name='Volatility'),
                    row=2, col=2
                )
            
            fig.update_layout(height=500, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("No financial data available. Try refreshing the data.")


def display_news_tab(app: CreditRiskMonitor, ticker: str):
    """Display news and sentiment tab"""
    
    # Get news data
    news_data = app.get_news_data(ticker, days=7)
    
    if news_data and news_data.get('latest_news'):
        news_list = news_data['latest_news']
        
        # Sentiment summary
        if news_list:
            sentiment_scores = [news['sentiment_score'] for news in news_list]
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Average Sentiment", f"{avg_sentiment:.3f}")
            
            with col2:
                positive_count = len([n for n in news_list if n['sentiment_label'] == 'positive'])
                st.metric("Positive Articles", positive_count)
            
            with col3:
                negative_count = len([n for n in news_list if n['sentiment_label'] == 'negative'])
                st.metric("Negative Articles", negative_count)
        
        # News articles
        st.subheader("📰 Recent News Articles")
        
        for news in news_list:
            # Determine alert class based on sentiment
            sentiment_class = ""
            if news['sentiment_score'] < -0.3:
                sentiment_class = "alert-high"
            elif news['sentiment_score'] < 0:
                sentiment_class = "alert-medium"
            else:
                sentiment_class = "alert-low"
            
            with st.container():
                st.markdown(f"""
                <div class="metric-card {sentiment_class}">
                    <h4>{news['headline']}</h4>
                    <p><strong>Sentiment:</strong> {news['sentiment_label'].title()} ({news['sentiment_score']:.3f})</p>
                    <p><strong>Event Type:</strong> {news.get('event_type', 'N/A')}</p>
                    <p><strong>Risk Score:</strong> {news.get('risk_score', 0):.3f}</p>
                    <p><strong>Published:</strong> {news['published_at'][:10]}</p>
                </div>
                """, unsafe_allow_html=True)
                st.write("---")
    
    else:
        st.info("No news data available. Try refreshing the data.")


def display_alerts_tab(app: CreditRiskMonitor, ticker: str):
    """Display alerts tab"""
    
    # Get alerts
    alerts = app.get_alerts(ticker, unread_only=False)
    
    if alerts:
        st.subheader("⚠️ System Alerts")
        
        # Alert summary
        severity_counts = {}
        for alert in alerts:
            severity = alert.get('severity', 'unknown')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Alerts", len(alerts))
        
        with col2:
            st.metric("Critical", severity_counts.get('critical', 0))
        
        with col3:
            st.metric("High", severity_counts.get('high', 0))
        
        with col4:
            st.metric("Medium", severity_counts.get('medium', 0))
        
        # Alert list
        for alert in alerts:
            severity = alert.get('severity', 'low')
            severity_color = {
                'critical': '#f44336',
                'high': '#ff9800',
                'medium': '#ffc107',
                'low': '#4caf50'
            }.get(severity, '#757575')
            
            with st.container():
                st.markdown(f"""
                <div class="metric-card" style="border-left-color: {severity_color};">
                    <h4>{alert['title']}</h4>
                    <p><strong>Severity:</strong> {severity.title()}</p>
                    <p><strong>Type:</strong> {alert['alert_type'].replace('_', ' ').title()}</p>
                    <p>{alert['message']}</p>
                    <p><strong>Created:</strong> {alert['created_at'][:19]}</p>
                    <p><strong>Status:</strong> {'Read' if alert['is_read'] else 'Unread'} | {'Acknowledged' if alert['is_acknowledged'] else 'Pending'}</p>
                </div>
                """, unsafe_allow_html=True)
                st.write("---")
    
    else:
        st.info("No alerts available.")


def display_leaderboard():
    """Display credit score leaderboard"""
    st.header("🏆 Credit Score Leaderboard")
    
    app = CreditRiskMonitor()
    leaderboard = app.get_leaderboard(limit=20)
    
    if leaderboard and leaderboard.get('entries'):
        entries = leaderboard['entries']
        
        # Create leaderboard table
        df = pd.DataFrame(entries)
        
        # Display top 10
        st.subheader("Top 10 Companies")
        
        for i, entry in enumerate(entries[:10], 1):
            col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
            
            with col1:
                st.write(f"**{i}.**")
            
            with col2:
                st.write(f"**{entry['ticker']}** - {entry['company_name']}")
            
            with col3:
                st.write(f"Score: **{entry['overall_score']:.1f}**")
            
            with col4:
                trend = entry.get('trend_direction', 'stable')
                trend_icon = {
                    'increasing': '📈',
                    'decreasing': '📉',
                    'stable': '➡️'
                }.get(trend, '➡️')
                st.write(f"{trend_icon} {trend.title()}")
        
        # Full leaderboard table
        st.subheader("Full Leaderboard")
        st.dataframe(df[['rank', 'ticker', 'company_name', 'overall_score', 'sector', 'trend_direction']])


if __name__ == "__main__":
    main()




