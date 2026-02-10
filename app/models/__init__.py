"""
Models Package
MongoDB document schemas and database connection
"""
from app.models.database import get_database, connect_to_mongo, close_mongo_connection
from app.models.face_model import FaceDocument, MerchantFaceDocument, VerificationLog

__all__ = [
    "get_database",
    "connect_to_mongo",
    "close_mongo_connection",
    "FaceDocument",
    "MerchantFaceDocument",
    "VerificationLog"
]
