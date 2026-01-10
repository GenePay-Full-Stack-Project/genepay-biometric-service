"""
Health Check Endpoints
Service status and monitoring
"""

from fastapi import APIRouter, Depends
from app.core.database import get_database

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "biometric-service"
    }


@router.get("/db")
async def database_health():
    """Database health check"""
    try:
        db = get_database()
        # Ping database
        await db.command('ping')
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }
