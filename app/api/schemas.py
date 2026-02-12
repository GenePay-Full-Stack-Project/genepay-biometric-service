"""
Pydantic schemas for API request/response validation
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime


class EnrollFaceRequest(BaseModel):
    """Request to enroll a new face"""
    user_id: Optional[int] = Field(None, description="User ID (for users)")
    merchant_id: Optional[int] = Field(None, description="Merchant ID (for merchants)")
    image_base64: str = Field(..., description="Base64 encoded face image")
    
    @validator('image_base64')
    def validate_image(cls, v):
        if not v or len(v) < 100:
            raise ValueError("Invalid image data")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123,
                "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
            }
        }


class EnrollFaceResponse(BaseModel):
    """Response from face enrollment"""
    success: bool
    message: str
    face_id: Optional[str] = None
    user_id: Optional[int] = None
    merchant_id: Optional[int] = None
    liveness_passed: bool = False
    liveness_confidence: Optional[float] = None
    quality_score: Optional[float] = None
    image_url: Optional[str] = None


class VerifyFaceRequest(BaseModel):
    """Request to verify a face"""
    user_id: Optional[int] = Field(None, description="User ID to verify against")
    merchant_id: Optional[int] = Field(None, description="Merchant ID to verify against")
    image_base64: str = Field(..., description="Base64 encoded face image for verification")
    require_liveness: bool = Field(True, description="Whether to require liveness check (enabled by default for security)")
    
    @validator('image_base64')
    def validate_image(cls, v):
        if not v or len(v) < 100:
            raise ValueError("Invalid image data")
        return v


class VerifyFaceResponse(BaseModel):
    """Response from face verification"""
    success: bool
    verified: bool
    message: str
    user_id: Optional[int] = None
    merchant_id: Optional[int] = None
    confidence: Optional[float] = None
    liveness_passed: bool = False
    liveness_confidence: Optional[float] = None
    match_distance: Optional[float] = None


class SearchFaceRequest(BaseModel):
    """Request to search for a face across all enrolled faces"""
    image_base64: str = Field(..., description="Base64 encoded face image to search")
    search_type: str = Field("user", description="Type: 'user' or 'merchant'")
    top_k: int = Field(5, description="Number of top matches to return", ge=1, le=20)
    min_confidence: float = Field(0.4, description="Minimum confidence threshold (40% for real-world conditions)", ge=0.0, le=1.0)
    merchant_id: Optional[int] = Field(None, description="Merchant ID performing the search (for logging)")


class FaceMatchResult(BaseModel):
    """Individual face match result"""
    user_id: Optional[int] = None
    merchant_id: Optional[int] = None
    confidence: float
    distance: float
    face_id: str


class SearchFaceResponse(BaseModel):
    """Response from face search"""
    success: bool
    message: str
    matches: List[FaceMatchResult] = []
    total_searched: int = 0


class DeleteFaceRequest(BaseModel):
    """Request to delete a face"""
    user_id: Optional[int] = None
    merchant_id: Optional[int] = None


class DeleteFaceResponse(BaseModel):
    """Response from face deletion"""
    success: bool
    message: str


class UpdateFaceUserRequest(BaseModel):
    """Request to update face document with user_id (called by payment service)"""
    user_id: int = Field(..., description="User ID to link to face")
    face_id: str = Field(..., description="Face ID from enrollment")


class UpdateFaceUserResponse(BaseModel):
    """Response from updating face with user_id"""
    success: bool
    message: str
    user_id: int
    face_id: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    timestamp: datetime
    mongodb_connected: bool
    s3_configured: bool


class MetricsResponse(BaseModel):
    """Service metrics response"""
    total_users: int = 0
    total_merchants: int = 0
    total_verifications: int = 0
    successful_verifications: int = 0
    failed_verifications: int = 0
    uptime: str = "0h 0m"
