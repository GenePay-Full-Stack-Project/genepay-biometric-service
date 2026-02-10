"""
Configuration Management
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "BioPay Biometric Service"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = False
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    
    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "biopay_biometric"
    
    # Face Recognition
    FACE_RECOGNITION_TOLERANCE: float = 0.6  # Lower is more strict
    FACE_ENCODING_MODEL: str = "small"  # 'small' (HOG - faster) or 'large' (CNN - more accurate)
    MIN_FACE_SIZE: int = 100  # Minimum face size in pixels
    
    # Continuous Learning
    ENABLE_CONTINUOUS_LEARNING: bool = True  # Add new encodings from successful verifications
    MAX_ENCODINGS_PER_USER: int = 10  # Maximum number of encodings to store per user
    MIN_CONFIDENCE_FOR_LEARNING: float = 0.55  # Only learn from high-confidence matches (55%+)
    LEARNING_UPDATE_INTERVAL: int = 3  # Update encodings every N successful verifications
    
    # Liveness Detection
    LIVENESS_THRESHOLD: float = 0.4  # Very lenient - only 40% of checks must pass (2 out of 5)
    ENABLE_LIVENESS_DETECTION: bool = False
    LIVENESS_MIN_SHARPNESS: float = 5.0  # Very low threshold - almost any image will pass
    LIVENESS_MIN_BRIGHTNESS: float = 20.0  # Very low for dark conditions
    LIVENESS_MAX_BRIGHTNESS: float = 250.0  # Very high for bright conditions
    
    # Security
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: str = "*"  # Changed to string to avoid JSON parsing issues
    
    # Payment Service
    PAYMENT_SERVICE_URL: str = "http://localhost:8080"
    API_GATEWAY_URL: str = "http://localhost:80"
    
    # Image Processing
    MAX_IMAGE_SIZE_MB: int = 5
    ALLOWED_IMAGE_FORMATS: list = ["JPEG", "PNG", "JPG"]
    PROCESSING_MAX_DIMENSION: int = 800  # Resize images larger than this for faster processing
    STORAGE_MAX_DIMENSION: int = 400  # Maximum size for stored anonymized images
    ANONYMIZATION_BLUR_STRENGTH: int = 25  # Blur strength for face anonymization
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
