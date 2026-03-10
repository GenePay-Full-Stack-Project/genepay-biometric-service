"""
Database Connection and Operations
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class Database:
    """MongoDB Database Manager"""
    
    client: AsyncIOMotorClient = None
    database: AsyncIOMotorDatabase = None


db = Database()


async def connect_to_mongo():
    """Connect to MongoDB"""
    try:
        logger.info(f"Connecting to MongoDB at {settings.MONGODB_URL}")
        db.client = AsyncIOMotorClient(settings.MONGODB_URL)
        db.database = db.client[settings.MONGODB_DATABASE]
        
        # Test connection
        await db.client.admin.command('ping')
        logger.info("✅ Successfully connected to MongoDB")
        
        # Create indexes
        await create_indexes()
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection():
    """Close MongoDB connection"""
    try:
        if db.client:
            db.client.close()
            logger.info("✅ MongoDB connection closed")
    except Exception as e:
        logger.error(f"❌ Error closing MongoDB connection: {e}")


async def create_indexes():
    """Create database indexes for performance"""
    try:
        # Faces collection indexes
        faces_collection = db.database.faces
        # Partial unique index: only enforce uniqueness when user_id is not null
        # This allows multiple pending enrollments (user_id=null) but ensures each user has only one active face
        await faces_collection.create_index(
            [("user_id", 1), ("is_active", 1)], 
            unique=True,
            partialFilterExpression={"user_id": {"$type": "number"}}
        )
        await faces_collection.create_index("is_active")
        await faces_collection.create_index("created_at")
        
        # Merchant faces collection indexes
        merchant_faces_collection = db.database.merchant_faces
        await merchant_faces_collection.create_index("merchant_id", unique=True)
        await merchant_faces_collection.create_index("is_active")
        await merchant_faces_collection.create_index("created_at")
        
        # Verification logs collection indexes
        verification_logs = db.database.verification_logs
        await verification_logs.create_index("user_id")
        await verification_logs.create_index("merchant_id")
        await verification_logs.create_index("timestamp")
        await verification_logs.create_index("success")
        
        logger.info("✅ Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"❌ Error creating indexes: {e}")


def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    return db.database
