# 📦 App Module

Main application package containing all core functionality for the Biometric Service.

## Overview

The `app` module is the heart of the Biometric Service. It contains all business logic, API routes, data models, and utility functions organized into logical sub-modules.

## 📁 Directory Structure

```
app/
├── __init__.py              # Package initialization
├── main.py                  # FastAPI application entry point
│
├── api/                     # 🔌 REST API Endpoints
│   ├── __init__.py
│   ├── routes.py            # Main route definitions
│   ├── endpoints/           # Individual endpoint modules
│   │   ├── faces.py
│   │   ├── verification.py
│   │   ├── health.py
│   │   └── metrics.py
│   └── schemas/             # Request/Response schemas
│       ├── request.py
│       └── response.py
│
├── services/                # 🧠 Business Logic
│   ├── __init__.py
│   ├── base_service.py      # Base service class
│   ├── face_service.py      # Face management
│   ├── recognition_service.py # Face recognition
│   ├── embedding_service.py # Embedding management
│   ├── storage_service.py   # AWS S3 operations
│   └── verification_service.py # Payment verification
│
├── models/                  # 💾 Data Models
│   ├── __init__.py
│   ├── base.py              # Base model classes
│   ├── face.py              # Face document
│   ├── embedding.py         # Face embedding
│   ├── verification_log.py  # Verification audit
│   └── merchant_face.py     # Merchant face linking
│
├── utils/                   # 🛠️ Utilities
│   ├── __init__.py
│   ├── image_utils.py       # Image processing
│   ├── validators.py        # Input validation
│   ├── security.py          # Authentication & crypto
│   ├── decorators.py        # Custom decorators
│   ├── exceptions.py        # Custom exceptions
│   ├── logger.py            # Logging setup
│   └── constants.py         # Application constants
│
└── config/                  # ⚙️ Configuration (optional)
    ├── __init__.py
    ├── settings.py          # Application settings
    └── database.py          # Database configuration
```

## 🏗️ Architecture Overview

### Request Flow

```
HTTP Request
    ↓
API Gateway (Nginx)
    ↓
FastAPI (main.py)
    ↓
Route Handler (api/endpoints/)
    ↓
Request Validation (api/schemas)
    ↓
Business Logic (services/)
    ↓
Data Models (models/)
    ↓
MongoDB / AWS S3
    ↓
Response Serialization
    ↓
HTTP Response
```

### Module Interactions

```
┌─────────────────┐
│     API         │  HTTP Endpoints
│  (api/)         │
└────────┬────────┘
         │
         ├─────────────────────────────────┬──────────────────────┐
         ↓                                 ↓                      ↓
┌─────────────────┐            ┌────────────────────┐   ┌──────────────┐
│   Services      │            │    Utils           │   │   Models     │
│  (services/)    │            │   (utils/)         │   │  (models/)   │
│                 │            │                    │   │              │
│ - Face Service  │            │ - Validators       │   │ - Face       │
│ - Recognition   │────────────│ - Image Utils      │───│ - Embedding  │
│ - Embedding     │            │ - Security         │   │ - Logs       │
│ - Storage       │            │ - Decorators       │   │ - Merchant   │
│ - Verification  │            │ - Exceptions       │   │              │
└────────┬────────┘            └────────────────────┘   └──────────────┘
         │
         ├─────────────────────────────────┐
         ↓                                 ↓
┌─────────────────┐           ┌───────────────────┐
│    MongoDB      │           │    AWS S3         │
│                 │           │                   │
│ - faces         │           │ - Face images     │
│ - embeddings    │           │ - Temp uploads    │
│ - logs          │           │                   │
└─────────────────┘           └───────────────────┘
```

## 🚀 Quick Start

### 1. Project Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings
```

### 2. Run Application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --port 8001

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 4
```

### 3. Access API

- **Interactive Docs:** http://localhost:8001/docs
- **ReDoc:** http://localhost:8001/redoc
- **OpenAPI JSON:** http://localhost:8001/openapi.json

## 📋 Module Descriptions

### 🔌 API Module (`api/`)

Handles HTTP request/response handling.

**Key Files:**
- `routes.py` - Route definitions and path parameters
- `endpoints/` - Individual endpoint implementations
- `schemas/` - Pydantic models for request/response validation

**See:** [API Module Documentation](./api/README.md)

### 🧠 Services Module (`services/`)

Contains all business logic and core functionality.

**Key Classes:**
- `FaceService` - Face registration, retrieval, deletion
- `RecognitionService` - Face detection and verification
- `EmbeddingService` - Embedding generation and comparison
- `StorageService` - AWS S3 operations
- `VerificationService` - Payment verification

**See:** [Services Module Documentation](./services/README.md)

### 💾 Models Module (`models/`)

MongoDB document models using Pydantic.

**Key Classes:**
- `Face` - Face document
- `FaceEmbedding` - Embedding vector
- `VerificationLog` - Audit log
- `MerchantFace` - Merchant linking

**See:** [Models Module Documentation](./models/README.md)

### 🛠️ Utils Module (`utils/`)

Reusable utilities and helper functions.

**Key Classes:**
- `ImageUtils` - Image processing
- `Validators` - Input validation
- `SecurityUtils` - JWT, encryption
- Custom decorators and exceptions

**See:** [Utils Module Documentation](./utils/README.md)

## 🔐 Security Features

✅ **Authentication**
- JWT token validation
- API key verification
- Request signing

✅ **Encryption**
- Password hashing with bcrypt
- Data encryption with AES
- HTTPS-only communication

✅ **Validation**
- Input sanitization
- Image format validation
- Embedding vector validation

✅ **Rate Limiting**
- Per-IP rate limiting
- Per-user rate limiting
- Endpoint-specific limits

## 📊 Configuration

### Environment Variables

```bash
# Application
APP_NAME=biometric-service
APP_VERSION=1.0.0
APP_ENV=development
DEBUG=True
PORT=8001

# Database
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=biopay_biometric

# AWS S3
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
S3_BUCKET_NAME=biopay-faces

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# Face Recognition
FACE_DETECTION_MODEL=hog
FACE_RECOGNITION_TOLERANCE=0.6
```

## 🧪 Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Run with Coverage
```bash
pytest tests/ --cov=app --cov-report=html
```

### Run Specific Test
```bash
pytest tests/test_api/test_face_endpoints.py -v
```

**See:** [Tests Module Documentation](../tests/README.md)

## 🔄 API Endpoints Summary

### Face Management
- `POST /api/v1/faces/register` - Register new face
- `GET /api/v1/faces/{face_id}` - Get face details
- `GET /api/v1/faces/user/{user_id}` - List user faces
- `DELETE /api/v1/faces/{face_id}` - Delete face

### Verification
- `POST /api/v1/faces/verify` - Verify face
- `GET /api/v1/verification-logs/{face_id}` - Get verification history

### System
- `GET /health` - Health check
- `GET /api/v1/metrics` - Service metrics

## 📦 Dependencies

**Core:**
- `fastapi>=0.109.0` - Web framework
- `pydantic>=2.5.3` - Data validation
- `uvicorn>=0.27.0` - ASGI server

**Face Recognition:**
- `face-recognition>=1.3.0` - Face detection/recognition
- `opencv-python>=4.9.0` - Image processing
- `numpy>=1.26.3` - Numerical computing

**Database:**
- `motor>=3.3.2` - Async MongoDB driver
- `pymongo>=4.6.1` - MongoDB client

**Security:**
- `python-jose>=3.3.0` - JWT handling
- `passlib>=1.7.4` - Password hashing
- `cryptography>=41.0.0` - Encryption

**Other:**
- `boto3>=1.34.34` - AWS S3 client
- `python-dotenv>=1.0.0` - Environment variables

## 🚀 Deployment

### Docker

```bash
# Build image
docker build -t biopay-biometric-service .

# Run container
docker run -p 8001:8001 \
  -e MONGODB_URL=mongodb://mongodb:27017 \
  -e AWS_ACCESS_KEY_ID=your_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret \
  biopay-biometric-service
```

### Docker Compose

```bash
# Start all services
cd backend
docker-compose up -d

# View logs
docker-compose logs -f biometric-service

# Stop services
docker-compose down
```

## 📚 Documentation Map

| Document | Purpose |
|----------|---------|
| [API Module](./api/README.md) | REST endpoints and schemas |
| [Services Module](./services/README.md) | Business logic |
| [Models Module](./models/README.md) | Data models |
| [Utils Module](./utils/README.md) | Utility functions |
| [Tests](../tests/README.md) | Test suite |
| [Main README](../README.md) | Service overview |

## 🆘 Troubleshooting

### MongoDB Connection Error
```python
# Check MongoDB is running
mongosh

# Check connection string in .env
MONGODB_URL=mongodb://localhost:27017
```

### Face Recognition Model Download
```bash
# Models download automatically, but can pre-download:
python -c "import face_recognition; face_recognition.face_encodings([])
"
```

### AWS S3 Credentials
```bash
# Verify credentials
aws s3 ls s3://your-bucket

# Or set in .env
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
```

## 🤝 Contributing

When contributing to the app module:

1. **Follow structure** - Keep code in appropriate module
2. **Type hints** - Add type hints to all functions
3. **Docstrings** - Document all public functions
4. **Tests** - Write tests for new features
5. **Follow conventions** - Use existing patterns
6. **Update documentation** - Update relevant READMEs

## 📞 Support

For questions or issues:
- Check relevant module README
- Review test examples
- Check main [README](../README.md)
- Open an issue on GitHub

---

**Last Updated:** 2025-11-12  
**Version:** 1.0.0  
**Status:** Active Development ✅
