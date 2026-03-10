"""
Face Model - MongoDB Document Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class FaceDocument(BaseModel):
    """Face document stored in MongoDB"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: Optional[int] = Field(None, description="User ID from payment service (None until linked)")
    face_encodings: List[List[float]] = Field(..., description="Multiple 128-dimensional face encodings from different angles/lighting")
    image_url: Optional[str] = Field(None, description="S3 URL of the face image")
    liveness_score: Optional[float] = Field(None, description="Liveness detection confidence")
    quality_score: Optional[float] = Field(None, description="Image quality score")
    metadata: Optional[dict] = Field(default_factory=lambda: {'learning_updates': 0}, description="Metadata including continuous learning stats")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class MerchantFaceDocument(BaseModel):
    """Merchant face document stored in MongoDB"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    merchant_id: int = Field(..., description="Merchant ID from payment service")
    face_encodings: List[List[float]] = Field(..., description="Multiple 128-dimensional face encodings from different angles/lighting")
    image_url: Optional[str] = Field(None, description="S3 URL of the face image")
    liveness_score: Optional[float] = Field(None, description="Liveness detection confidence")
    quality_score: Optional[float] = Field(None, description="Image quality score")
    metadata: Optional[dict] = Field(default_factory=lambda: {'learning_updates': 0}, description="Metadata including continuous learning stats")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class VerificationLog(BaseModel):
    """Verification attempt log"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: Optional[int] = Field(None)
    merchant_id: Optional[int] = Field(None)
    success: bool
    confidence: Optional[float] = Field(None)
    liveness_passed: bool = Field(default=False)
    metadata: Optional[dict] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
