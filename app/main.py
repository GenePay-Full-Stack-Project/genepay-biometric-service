"""
Biometric Service - Main Application Entry Point
Handles face recognition, registration, and verification with liveness detection
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime

from app.config import settings
from app.models.database import connect_to_mongo, close_mongo_connection, get_database
from app.api.biometric import router as biometric_router
from app.api.schemas import HealthResponse, MetricsResponse

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Reduce MongoDB driver debug logging
logging.getLogger("pymongo").setLevel(logging.WARNING)
logging.getLogger("pymongo.topology").setLevel(logging.WARNING)
logging.getLogger("pymongo.connection").setLevel(logging.WARNING)
logging.getLogger("pymongo.serverSelection").setLevel(logging.WARNING)

# Track service start time
service_start_time = datetime.utcnow()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting BioPay Biometric Service...")
    logger.info(f"Environment: {'Development' if settings.DEBUG else 'Production'}")
    
    try:
        # Initialize database connections
        await connect_to_mongo()
        logger.info("✅ Database initialized")
        
        # Log face recognition settings
        logger.info(f"Face recognition tolerance: {settings.FACE_RECOGNITION_TOLERANCE}")
        logger.info(f"Liveness detection: {'Enabled' if settings.ENABLE_LIVENESS_DETECTION else 'Disabled'}")
        
        logger.info("✅ Biometric Service is ready!")
        
    except Exception as e:
        logger.error(f"❌ Failed to start service: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Biometric Service...")
    try:
        await close_mongo_connection()
        logger.info("✅ Service shutdown complete")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")


app = FastAPI(
    title="BioPay Biometric Service",
    description="Face recognition and verification service with liveness detection for BioPay payment system",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(biometric_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "documentation": "/docs",
        "features": [
            "Face enrollment with liveness detection",
            "Face verification",
            "Face search",
            "Multiple quality checks"
        ]
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        db = get_database()
        # Try to ping database
        await db.command('ping')
        mongodb_connected = True
    except:
        mongodb_connected = False
    
    return HealthResponse(
        status="healthy" if mongodb_connected else "degraded",
        service="biometric-service",
        timestamp=datetime.utcnow(),
        mongodb_connected=mongodb_connected,
        s3_configured=False
    )


@app.get("/metrics", response_model=MetricsResponse)
async def metrics():
    """Service metrics endpoint"""
    try:
        db = get_database()
        
        # Count enrolled faces
        total_users = await db.faces.count_documents({"is_active": True})
        total_merchants = await db.merchant_faces.count_documents({"is_active": True})
        
        # Count verifications
        total_verifications = await db.verification_logs.count_documents({})
        successful_verifications = await db.verification_logs.count_documents({"success": True})
        failed_verifications = total_verifications - successful_verifications
        
        # Calculate uptime
        uptime_delta = datetime.utcnow() - service_start_time
        hours = uptime_delta.seconds // 3600
        minutes = (uptime_delta.seconds % 3600) // 60
        uptime = f"{uptime_delta.days}d {hours}h {minutes}m"
        
        return MetricsResponse(
            total_users=total_users,
            total_merchants=total_merchants,
            total_verifications=total_verifications,
            successful_verifications=successful_verifications,
            failed_verifications=failed_verifications,
            uptime=uptime
        )
        
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        return MetricsResponse(uptime="0h 0m")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
