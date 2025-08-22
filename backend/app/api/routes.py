from fastapi import APIRouter
from app.api.endpoints import companies, data, scoring, news, alerts

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(data.router, prefix="/data", tags=["data"])
api_router.include_router(scoring.router, prefix="/scoring", tags=["scoring"])
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])




