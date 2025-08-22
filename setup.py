#!/usr/bin/env python3
"""
Setup script for News-Driven Credit Risk Monitor
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a shell command with error handling"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing dependencies...")
    
    # Install backend dependencies
    if not run_command("cd backend && pip install -r requirements.txt", "Installing backend dependencies"):
        return False
    
    # Install frontend dependencies
    if not run_command("cd frontend && pip install -r requirements.txt", "Installing frontend dependencies"):
        return False
    
    return True

def setup_environment():
    """Setup environment configuration"""
    print("\n⚙️ Setting up environment...")
    
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from template")
        print("⚠️  Please edit .env file with your API keys")
    elif env_file.exists():
        print("✅ .env file already exists")
    else:
        print("❌ Could not find env.example file")
        return False
    
    return True

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = [
        "database",
        "logs",
        "data",
        "nginx",
        "nginx/ssl"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created {directory}/ directory")
    
    return True

def setup_database():
    """Setup database"""
    print("\n🗄️ Setting up database...")
    
    # Create database directory if it doesn't exist
    Path("database").mkdir(exist_ok=True)
    
    # Create init.sql for PostgreSQL
    init_sql = """-- Database initialization script
CREATE DATABASE IF NOT EXISTS credit_monitor;
"""
    
    with open("database/init.sql", "w") as f:
        f.write(init_sql)
    
    print("✅ Database setup completed")
    return True

def create_nginx_config():
    """Create Nginx configuration"""
    print("\n🌐 Creating Nginx configuration...")
    
    nginx_config = """events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }
    
    upstream frontend {
        server frontend:8501;
    }
    
    server {
        listen 80;
        server_name localhost;
        
        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Backend API
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Health checks
        location /health {
            proxy_pass http://backend/health;
        }
    }
}
"""
    
    Path("nginx").mkdir(exist_ok=True)
    with open("nginx/nginx.conf", "w") as f:
        f.write(nginx_config)
    
    print("✅ Nginx configuration created")
    return True

def create_sample_data():
    """Create sample data for testing"""
    print("\n📊 Creating sample data...")
    
    sample_companies = [
        {
            "ticker": "AAPL",
            "name": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics"
        },
        {
            "ticker": "MSFT",
            "name": "Microsoft Corporation",
            "sector": "Technology",
            "industry": "Software"
        },
        {
            "ticker": "GOOGL",
            "name": "Alphabet Inc.",
            "sector": "Technology",
            "industry": "Internet Services"
        },
        {
            "ticker": "AMZN",
            "name": "Amazon.com Inc.",
            "sector": "Consumer Cyclical",
            "industry": "Internet Retail"
        },
        {
            "ticker": "TSLA",
            "name": "Tesla Inc.",
            "sector": "Consumer Cyclical",
            "industry": "Auto Manufacturers"
        }
    ]
    
    sample_data = {
        "companies": sample_companies
    }
    
    with open("data/sample_data.json", "w") as f:
        import json
        json.dump(sample_data, f, indent=2)
    
    print("✅ Sample data created")
    return True

def create_startup_scripts():
    """Create startup scripts"""
    print("\n🚀 Creating startup scripts...")
    
    # Windows batch file
    windows_script = """@echo off
echo Starting News-Driven Credit Risk Monitor...
echo.
echo Backend API: http://localhost:8000
echo Frontend Dashboard: http://localhost:8501
echo.
echo Press Ctrl+C to stop
echo.
docker-compose up
"""
    
    with open("start.bat", "w") as f:
        f.write(windows_script)
    
    # Unix shell script
    unix_script = """#!/bin/bash
echo "Starting News-Driven Credit Risk Monitor..."
echo ""
echo "Backend API: http://localhost:8000"
echo "Frontend Dashboard: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop"
echo ""
docker-compose up
"""
    
    with open("start.sh", "w") as f:
        f.write(unix_script)
    
    # Make shell script executable
    os.chmod("start.sh", 0o755)
    
    print("✅ Startup scripts created")
    return True

def main():
    """Main setup function"""
    print("🏗️ News-Driven Credit Risk Monitor Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        sys.exit(1)
    
    # Setup database
    if not setup_database():
        sys.exit(1)
    
    # Create Nginx config
    if not create_nginx_config():
        sys.exit(1)
    
    # Create sample data
    if not create_sample_data():
        sys.exit(1)
    
    # Create startup scripts
    if not create_startup_scripts():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your API keys:")
    print("   - Alpha Vantage: https://www.alphavantage.co/support/#api-key")
    print("   - NewsAPI: https://newsapi.org/register")
    print("   - FRED API: https://fred.stlouisfed.org/docs/api/api_key.html")
    print("   - Yahoo Finance: No API key required")
    print("2. Run 'docker-compose up' to start the application")
    print("3. Access the dashboard at http://localhost:8501")
    print("4. Access the API at http://localhost:8000")
    print("\n📚 For more information, see README.md")

if __name__ == "__main__":
    main()



