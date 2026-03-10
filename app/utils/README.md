# 🛠️ Utils Module

Utility functions and helper tools for the Biometric Service.

## Overview

This module contains reusable utility functions, decorators, middleware, and helpers that support the main application logic.

## 📁 Structure

```
utils/
├── __init__.py                  # Module initialization
├── image_utils.py              # Image processing
├── validators.py               # Input validation
├── security.py                 # Authentication & encryption
├── decorators.py               # Custom decorators
├── exceptions.py               # Custom exceptions
├── logger.py                   # Logging configuration
└── constants.py                # Application constants
```

## 🖼️ Image Utils

**File:** `image_utils.py`

Image processing and validation utilities.

```python
class ImageUtils:
    """Image processing utilities"""
    
    @staticmethod
    def load_image(file_path: str) -> np.ndarray:
        """Load image from file"""
        
    @staticmethod
    def load_image_from_bytes(image_bytes: bytes) -> np.ndarray:
        """Convert bytes to image array"""
        
    @staticmethod
    def save_image(image: np.ndarray, output_path: str) -> None:
        """Save image to file"""
        
    @staticmethod
    def resize_image(
        image: np.ndarray,
        size: Tuple[int, int]
    ) -> np.ndarray:
        """Resize image to specific dimensions"""
        
    @staticmethod
    def normalize_image(image: np.ndarray) -> np.ndarray:
        """Normalize image pixel values"""
        
    @staticmethod
    def rotate_image(
        image: np.ndarray,
        angle: int
    ) -> np.ndarray:
        """Rotate image by angle"""
        
    @staticmethod
    def convert_to_rgb(image: np.ndarray) -> np.ndarray:
        """Convert image to RGB format"""
```

**Usage:**
```python
from utils.image_utils import ImageUtils

# Load image
img = ImageUtils.load_image("path/to/image.jpg")

# Load from bytes
img = ImageUtils.load_image_from_bytes(image_bytes)

# Resize
resized = ImageUtils.resize_image(img, (224, 224))

# Normalize
normalized = ImageUtils.normalize_image(img)

# Convert format
rgb_img = ImageUtils.convert_to_rgb(img)
```

## ✅ Validators

**File:** `validators.py`

Input validation functions.

```python
class Validators:
    """Input validation utilities"""
    
    @staticmethod
    def validate_image_file(file: UploadFile) -> bool:
        """Validate image file format and size"""
        
    @staticmethod
    def validate_user_id(user_id: str) -> bool:
        """Validate user ID format"""
        
    @staticmethod
    def validate_face_id(face_id: str) -> bool:
        """Validate face ID format"""
        
    @staticmethod
    def validate_embedding(embedding: List[float]) -> bool:
        """Validate embedding vector"""
        
    @staticmethod
    def validate_confidence(confidence: float) -> bool:
        """Validate confidence score (0-1)"""
        
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email address"""
```

**Usage:**
```python
from utils.validators import Validators

# Validate image
if not Validators.validate_image_file(uploaded_file):
    raise ValueError("Invalid image format")

# Validate user ID
if not Validators.validate_user_id(user_id):
    raise ValueError("Invalid user ID")

# Validate confidence
if not Validators.validate_confidence(score):
    raise ValueError("Confidence must be 0-1")
```

**Validation Rules:**

| Field | Rules |
|-------|-------|
| **Image** | Format: JPG, PNG, JPEG; Size: < 10MB; Dimensions: 100x100 to 8000x8000 |
| **user_id** | Non-empty, alphanumeric + underscore, length 3-50 |
| **face_id** | Must start with "face_", alphanumeric + underscore |
| **embedding** | List of exactly 128 floats |
| **confidence** | Float between 0.0 and 1.0 |

## 🔐 Security Utils

**File:** `security.py`

Authentication, encryption, and security utilities.

```python
class SecurityUtils:
    """Security utilities"""
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate secure API key"""
        
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        
    @staticmethod
    def verify_password(
        password: str,
        password_hash: str
    ) -> bool:
        """Verify password against hash"""
        
    @staticmethod
    def create_jwt_token(
        data: dict,
        expires_in: int = 3600
    ) -> str:
        """Create JWT token"""
        
    @staticmethod
    def verify_jwt_token(token: str) -> dict:
        """Verify and decode JWT token"""
        
    @staticmethod
    def encrypt_data(data: str, key: str) -> str:
        """Encrypt data using AES"""
        
    @staticmethod
    def decrypt_data(encrypted: str, key: str) -> str:
        """Decrypt encrypted data"""
```

**Usage:**
```python
from utils.security import SecurityUtils

# Generate API key
api_key = SecurityUtils.generate_api_key()

# Hash password
hashed = SecurityUtils.hash_password("user_password")

# Verify password
if SecurityUtils.verify_password("input_password", hashed):
    print("Password correct")

# JWT operations
token = SecurityUtils.create_jwt_token({"user_id": "123"})
payload = SecurityUtils.verify_jwt_token(token)
```

## 🎭 Decorators

**File:** `decorators.py`

Custom decorators for common functionality.

```python
from functools import wraps

def require_api_key(func):
    """Decorator to require API key"""
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        api_key = request.headers.get("X-API-Key")
        if not api_key or not verify_api_key(api_key):
            raise HTTPException(status_code=401, detail="Invalid API key")
        return await func(request, *args, **kwargs)
    return wrapper

def require_auth(func):
    """Decorator to require JWT authentication"""
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        try:
            payload = SecurityUtils.verify_jwt_token(token)
            request.state.user = payload
        except:
            raise HTTPException(status_code=401, detail="Invalid token")
        return await func(request, *args, **kwargs)
    return wrapper

def log_execution(func):
    """Decorator to log function execution"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        logger.info(f"Executing: {func.__name__}")
        result = await func(*args, **kwargs)
        logger.info(f"Completed: {func.__name__}")
        return result
    return wrapper

def handle_exceptions(func):
    """Decorator to handle exceptions gracefully"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
    return wrapper
```

**Usage:**
```python
from utils.decorators import require_api_key, require_auth, log_execution

@app.post("/api/v1/faces/register")
@require_api_key
@log_execution
@handle_exceptions
async def register_face(request: Request):
    return {"status": "registered"}
```

## ❌ Custom Exceptions

**File:** `exceptions.py`

Custom exception classes.

```python
class BiometricServiceException(Exception):
    """Base exception"""
    pass

class InvalidImageException(BiometricServiceException):
    """Raised when image is invalid"""
    pass

class FaceNotDetectedException(BiometricServiceException):
    """Raised when no face detected"""
    pass

class VerificationFailedException(BiometricServiceException):
    """Raised when verification fails"""
    pass

class StorageException(BiometricServiceException):
    """Raised for storage operations"""
    pass

class DatabaseException(BiometricServiceException):
    """Raised for database operations"""
    pass
```

**Usage:**
```python
from utils.exceptions import InvalidImageException, FaceNotDetectedException

try:
    faces = recognize_faces(image)
    if not faces:
        raise FaceNotDetectedException("No face detected in image")
except FaceNotDetectedException as e:
    logger.error(f"Face detection failed: {str(e)}")
    return {"error": "No face detected"}
```

## 📝 Logger

**File:** `logger.py`

Centralized logging configuration.

```python
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(name: str, log_level: str = "INFO") -> logging.Logger:
    """Setup logger with file and console handlers"""
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # File handler
    file_handler = RotatingFileHandler(
        f"logs/{name}.log",
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger
```

**Usage:**
```python
from utils.logger import setup_logger

logger = setup_logger(__name__)
logger.info("Application started")
logger.error("An error occurred")
logger.debug("Debug information")
```

## 🔧 Constants

**File:** `constants.py`

Application-wide constants.

```python
# Image Processing
SUPPORTED_IMAGE_FORMATS = {"jpg", "jpeg", "png"}
MAX_IMAGE_SIZE_MB = 10
MIN_IMAGE_WIDTH = 100
MIN_IMAGE_HEIGHT = 100
MAX_IMAGE_WIDTH = 8000
MAX_IMAGE_HEIGHT = 8000

# Face Recognition
FACE_DETECTION_MODEL = "hog"  # or "cnn"
FACE_RECOGNITION_TOLERANCE = 0.6
EMBEDDING_DIMENSION = 128
MIN_CONFIDENCE = 0.6

# Database
MONGODB_TIMEOUT = 30
COLLECTION_NAMES = {
    "faces": "faces",
    "embeddings": "embeddings",
    "verification_logs": "verification_logs"
}

# API
API_VERSION = "v1"
MAX_RETRY_ATTEMPTS = 3
REQUEST_TIMEOUT = 30

# Security
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_SECONDS = 86400  # 24 hours
```

**Usage:**
```python
from utils.constants import (
    SUPPORTED_IMAGE_FORMATS,
    EMBEDDING_DIMENSION,
    MIN_CONFIDENCE
)

if file_format not in SUPPORTED_IMAGE_FORMATS:
    raise ValueError("Unsupported format")

if embedding.shape[0] != EMBEDDING_DIMENSION:
    raise ValueError("Invalid embedding dimension")
```

## 🧪 Testing Utilities

```python
# tests/test_utils.py
import pytest
from utils.image_utils import ImageUtils
from utils.validators import Validators

def test_image_resize():
    img = ImageUtils.load_image("test.jpg")
    resized = ImageUtils.resize_image(img, (224, 224))
    assert resized.shape == (224, 224, 3)

def test_user_id_validation():
    assert Validators.validate_user_id("user_123") == True
    assert Validators.validate_user_id("") == False
    assert Validators.validate_user_id("user 123") == False
```

## 📚 Best Practices

✅ **Do:**
- Keep utilities focused and single-responsibility
- Add type hints to all functions
- Include docstrings with examples
- Write tests for utilities
- Use constants instead of magic numbers

❌ **Don't:**
- Create god-utilities with too many functions
- Mix business logic with utilities
- Skip documentation
- Add dependencies without need

## 🔗 Related Documentation

- [Services Layer](../services/README.md)
- [API Routes](../api/README.md)
- [Models](../models/README.md)

---

**Last Updated:** 2025-11-12
