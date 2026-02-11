# 🧠 Services Module

Business logic and core functionality for face recognition operations.

## Overview

This module contains all business logic separate from API routes. Services handle face processing, embedding generation, verification, and database operations.

## 📁 Structure

```
services/
├── __init__.py                  # Module initialization
├── face_service.py             # Face management logic
├── recognition_service.py      # Face recognition & verification
├── embedding_service.py        # Embedding generation & storage
├── storage_service.py          # AWS S3 file operations
├── verification_service.py     # Verification logic & audit
└── base_service.py             # Base service class
```

## 🔑 Core Services

### Face Service
**File:** `face_service.py`

Handles CRUD operations for face records.

```python
class FaceService:
    """Manage face records"""
    
    async def register_face(
        self,
        user_id: str,
        image: UploadFile,
        label: str = "primary"
    ) -> Face:
        """Register new face for user"""
        
    async def get_face(self, face_id: str) -> Optional[Face]:
        """Retrieve face by ID"""
        
    async def list_user_faces(self, user_id: str) -> List[Face]:
        """Get all faces for user"""
        
    async def delete_face(self, face_id: str) -> bool:
        """Delete face record"""
        
    async def update_face_label(
        self,
        face_id: str,
        label: str
    ) -> Face:
        """Update face label"""
```

**Usage:**
```python
face_service = FaceService()

# Register
face = await face_service.register_face(
    user_id="user_123",
    image=uploaded_file,
    label="primary"
)

# Retrieve
face = await face_service.get_face("face_abc123")

# List
user_faces = await face_service.list_user_faces("user_123")
```

### Recognition Service
**File:** `recognition_service.py`

Handles face detection and recognition using face_recognition library.

```python
class RecognitionService:
    """Face detection and recognition"""
    
    async def detect_faces(self, image: np.ndarray) -> List[np.ndarray]:
        """Detect all faces in image"""
        
    async def extract_embedding(self, image: np.ndarray) -> np.ndarray:
        """Extract face embedding (128-dim vector)"""
        
    async def compare_faces(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray,
        tolerance: float = 0.6
    ) -> float:
        """Compare two embeddings, return distance"""
        
    async def verify_face(
        self,
        test_image: np.ndarray,
        reference_embedding: np.ndarray
    ) -> Dict[str, any]:
        """Verify if face matches embedding"""
```

**Usage:**
```python
recognition = RecognitionService()

# Detect faces
faces = await recognition.detect_faces(image_array)

# Extract embedding
embedding = await recognition.extract_embedding(face_region)

# Compare
distance = await recognition.compare_faces(
    embedding1, embedding2
)

# Verify
result = await recognition.verify_face(
    test_image, stored_embedding
)
# Returns: {match: True, distance: 0.05, confidence: 0.95}
```

### Embedding Service
**File:** `embedding_service.py`

Manages embedding vectors and similarity calculations.

```python
class EmbeddingService:
    """Manage face embeddings"""
    
    async def store_embedding(
        self,
        face_id: str,
        embedding: List[float],
        model_version: str
    ) -> EmbeddingRecord:
        """Store embedding in database"""
        
    async def get_embedding(self, face_id: str) -> Optional[List[float]]:
        """Retrieve embedding for face"""
        
    async def find_similar_faces(
        self,
        embedding: List[float],
        threshold: float = 0.6,
        limit: int = 10
    ) -> List[Face]:
        """Find similar faces using vector similarity"""
        
    async def calculate_distance(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """Calculate Euclidean distance"""
```

**Usage:**
```python
embedding_service = EmbeddingService()

# Store
await embedding_service.store_embedding(
    face_id="face_123",
    embedding=embedding_vector,
    model_version="model_v1.0"
)

# Find similar
similar = await embedding_service.find_similar_faces(
    embedding=new_embedding,
    threshold=0.6
)
```

### Storage Service
**File:** `storage_service.py`

Handles AWS S3 operations for image storage.

```python
class StorageService:
    """AWS S3 file operations"""
    
    async def upload_image(
        self,
        file: UploadFile,
        folder: str = "faces"
    ) -> str:
        """Upload image to S3, return URL"""
        
    async def download_image(self, s3_url: str) -> bytes:
        """Download image from S3"""
        
    async def delete_image(self, s3_url: str) -> bool:
        """Delete image from S3"""
        
    async def get_presigned_url(
        self,
        s3_url: str,
        expiration: int = 3600
    ) -> str:
        """Generate presigned URL (valid for 1 hour)"""
```

**Usage:**
```python
storage = StorageService()

# Upload
s3_url = await storage.upload_image(
    file=uploaded_file,
    folder="faces"
)

# Get presigned URL
presigned = await storage.get_presigned_url(s3_url)
```

### Verification Service
**File:** `verification_service.py`

Handles payment verification and audit logging.

```python
class VerificationService:
    """Face verification for payments"""
    
    async def verify_for_payment(
        self,
        face_id: str,
        test_image: np.ndarray,
        merchant_id: str
    ) -> Dict:
        """Verify face for payment processing"""
        
    async def log_verification(
        self,
        face_id: str,
        match: bool,
        confidence: float,
        error: Optional[str] = None
    ) -> VerificationLog:
        """Log verification attempt for audit"""
        
    async def get_verification_history(
        self,
        face_id: str,
        limit: int = 100
    ) -> List[VerificationLog]:
        """Get verification audit trail"""
```

**Usage:**
```python
verification = VerificationService()

# Verify payment
result = await verification.verify_for_payment(
    face_id="face_123",
    test_image=captured_image,
    merchant_id="merchant_456"
)

# Get history
history = await verification.get_verification_history(
    face_id="face_123",
    limit=50
)
```

## 🏗️ Base Service

**File:** `base_service.py`

Common functionality for all services.

```python
class BaseService:
    """Base class for all services"""
    
    def __init__(self):
        self.db = get_mongodb_connection()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def close(self):
        """Close connections"""
        await self.db.close()
```

## 🔄 Service Interactions

```
API Request
    ↓
├─ Face Registration Flow
│  └─ API → FaceService → RecognitionService → EmbeddingService → StorageService
│
├─ Face Verification Flow
│  └─ API → VerificationService → RecognitionService → EmbeddingService
│
└─ Face Retrieval Flow
   └─ API → FaceService → StorageService
```

## 🛠️ Dependency Injection

Services should be injected via dependency injection:

```python
from fastapi import FastAPI, Depends
from services.face_service import FaceService

app = FastAPI()

async def get_face_service() -> FaceService:
    service = FaceService()
    yield service
    await service.close()

@app.post("/api/v1/faces/register")
async def register(
    face_service: FaceService = Depends(get_face_service)
):
    return await face_service.register_face(...)
```

## ⚡ Performance Considerations

### Async Operations
```python
# All services are async
async def long_running_task():
    # Non-blocking I/O
    result = await db.insert_one(document)
    return result
```

### Caching
```python
# Cache face embeddings
from functools import lru_cache

@lru_cache(maxsize=1000)
async def get_embedding_cached(face_id: str):
    return await embedding_service.get_embedding(face_id)
```

### Batch Operations
```python
# Process multiple faces efficiently
async def batch_verify(faces: List[Face]):
    tasks = [verify_face(face) for face in faces]
    return await asyncio.gather(*tasks)
```

## 🧪 Testing Services

```python
# tests/test_face_service.py
import pytest
from services.face_service import FaceService

@pytest.fixture
async def face_service():
    service = FaceService()
    yield service
    await service.close()

@pytest.mark.asyncio
async def test_register_face(face_service):
    result = await face_service.register_face(
        user_id="test_user",
        image=mock_image,
        label="test"
    )
    assert result.face_id is not None
```

## 📝 Creating New Services

1. **Create file** in `services/` directory
2. **Inherit from** `BaseService`
3. **Implement** business logic methods
4. **Add** error handling
5. **Use** async/await
6. **Document** with docstrings
7. **Write** tests

Example:
```python
# services/custom_service.py
from services.base_service import BaseService

class CustomService(BaseService):
    """Custom business logic"""
    
    async def process_data(self, data: dict) -> dict:
        """Process data"""
        self.logger.info(f"Processing: {data}")
        result = await self.db.process(data)
        return result
```

## 🔗 Related Documentation

- [API Routes](../api/README.md)
- [Data Models](../models/README.md)
- [Utilities](../utils/README.md)

---

**Last Updated:** 2025-11-12
