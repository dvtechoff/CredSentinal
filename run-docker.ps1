Write-Host "🚀 News-Driven Credit Risk Monitor - Docker Launcher" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Choose your deployment option:" -ForegroundColor Yellow
Write-Host "1. Development (SQLite) - Quick start, no external database needed" -ForegroundColor White
Write-Host "2. Production (PostgreSQL + Redis + Nginx) - Full stack deployment" -ForegroundColor White
Write-Host "3. Backend only (SQLite) - Just the API" -ForegroundColor White
Write-Host "4. Frontend only - Just the dashboard" -ForegroundColor White
Write-Host ""
$choice = Read-Host "Enter your choice (1-4)"

switch ($choice) {
    "1" {
        Write-Host "Starting development environment with SQLite..." -ForegroundColor Green
        docker-compose -f docker-compose.dev.yml up --build
    }
    "2" {
        Write-Host "Starting production environment with PostgreSQL..." -ForegroundColor Green
        docker-compose up --build
    }
    "3" {
        Write-Host "Starting backend only..." -ForegroundColor Green
        docker-compose -f docker-compose.dev.yml up --build backend
    }
    "4" {
        Write-Host "Starting frontend only..." -ForegroundColor Green
        docker-compose -f docker-compose.dev.yml up --build frontend
    }
    default {
        Write-Host "Invalid choice. Please run the script again." -ForegroundColor Red
        exit 1
    }
}
