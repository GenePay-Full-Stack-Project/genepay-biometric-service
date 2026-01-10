"""
Biometric Data Models
MongoDB document schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class FaceEncoding(BaseModel):
    """Face encoding vector (128-dimensional)"""
    encoding: List[float]
    model: str = "large"


class BiometricData(BaseModel):
    """User biometric data stored in MongoDB"""
    user_id: str = Field(..., description="User ID from payment service")
    face_id: str = Field(..., description="Unique face ID")
    face_encoding: FaceEncoding = Field(..., description="Face encoding vector")
    image_url: Optional[str] = Field(None, description="S3 URL for face image")
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "face_id": "face_abc123",
                "face_encoding": {
                    "encoding": [0.1, 0.2, 0.3],
                    "model": "large"
                },
                "image_url": "https://s3.amazonaws.com/bucket/face.jpg",
                "is_active": True
            }
        }


class VerificationLog(BaseModel):
    """Face verification attempt log"""
    user_id: str
    face_id: str
    verified_at: datetime = Field(default_factory=datetime.utcnow)
    match_result: bool
    confidence_score: float
    ip_address: Optional[str] = None
