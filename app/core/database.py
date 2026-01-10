"""
MongoDB Database Connection
"""

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

# Global MongoDB client and database
mongo_client: AsyncIOMotorClient = None
database = None


async def connect_to_mongo():
    """Connect to MongoDB"""
    global mongo_client, database
    mongo_client = AsyncIOMotorClient(settings.MONGODB_URL)
    database = mongo_client[settings.MONGODB_DB_NAME]
    
    # Test connection
    await mongo_client.admin.command('ping')


async def close_mongo_connection():
    """Close MongoDB connection"""
    global mongo_client
    if mongo_client:
        mongo_client.close()


def get_database():
    """Get database instance"""
    return database
