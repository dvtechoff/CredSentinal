#!/bin/bash

echo "🚀 News-Driven Credit Risk Monitor - Docker Launcher"
echo "=================================================="
echo ""
echo "Choose your deployment option:"
echo "1. Development (SQLite) - Quick start, no external database needed"
echo "2. Production (PostgreSQL + Redis + Nginx) - Full stack deployment"
echo "3. Backend only (SQLite) - Just the API"
echo "4. Frontend only - Just the dashboard"
echo ""
read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo "Starting development environment with SQLite..."
        docker-compose -f docker-compose.dev.yml up --build
        ;;
    2)
        echo "Starting production environment with PostgreSQL..."
        docker-compose up --build
        ;;
    3)
        echo "Starting backend only..."
        docker-compose -f docker-compose.dev.yml up --build backend
        ;;
    4)
        echo "Starting frontend only..."
        docker-compose -f docker-compose.dev.yml up --build frontend
        ;;
    *)
        echo "Invalid choice. Please run the script again."
        exit 1
        ;;
esac
