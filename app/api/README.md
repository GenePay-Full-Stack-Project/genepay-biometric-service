# 🔌 API Module

REST API endpoints for the Biometric Service.

## Overview

This module contains all FastAPI route handlers and endpoint definitions for face registration, verification, and management operations.

## 📁 Structure

```
api/
├── __init__.py          # Module initialization
├── routes.py            # Main API route definitions
├── endpoints/
│   ├── faces.py        # Face-related endpoints
│   ├── verification.py # Verification endpoints
│   ├── health.py       # Health check endpoints
│   └── metrics.py      # Service metrics endpoints
└── schemas/
    ├── request.py      # Request body schemas
    └── response.py     # Response body schemas
```

## 🚀 Key Features

### Face Endpoints
- **POST /api/v1/faces/register** - Register new face
- **POST /api/v1/faces/verify** - Verify face
- **GET /api/v1/faces/{face_id}** - Get face details
- **DELETE /api/v1/faces/{face_id}** - Delete face record

### Health Endpoints
- **GET /health** - Service health check
- **GET /api/v1/health** - Detailed health status

### Metrics Endpoints
- **GET /api/v1/metrics** - Service metrics

## 📋 Request/Response Examples

### Register Face
```json
POST /api/v1/faces/register
Content-Type: multipart/form-data

{
  "image": <binary>,
  "user_id": "user_123",
  "label": "primary_face"
}

Response:
{
  "face_id": "face_abc123",
  "user_id": "user_123",
  "embedding_size": 128,
  "created_at": "2025-11-12T10:30:00Z"
}
```

### Verify Face
```json
POST /api/v1/faces/verify
Content-Type: multipart/form-data

{
  "image": <binary>,
  "face_id": "face_abc123"
}

Response:
{
  "match": true,
  "confidence": 0.95,
  "distance": 0.05,
  "verified_at": "2025-11-12T10:35:00Z"
}
```

## 🔐 Authentication

All endpoints require either:
- **API Key** in `X-API-Key` header
- **JWT Token** in `Authorization` header

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8001/api/v1/faces
```

## 🛠️ Error Handling

All endpoints return consistent error responses:

```json
{
  "error": "Invalid image format",
  "code": "INVALID_IMAGE",
  "status": 400,
  "timestamp": "2025-11-12T10:30:00Z"
}
```

### Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad request
- `401` - Unauthorized
- `404` - Not found
- `422` - Validation error
- `500` - Server error

## 📚 API Documentation

Access interactive API docs at:
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **OpenAPI JSON**: http://localhost:8001/openapi.json

## 🧪 Testing

```bash
# Test face registration
curl -X POST http://localhost:8001/api/v1/faces/register \
  -F "image=@face.jpg" \
  -F "user_id=user_123"

# Test face verification
curl -X POST http://localhost:8001/api/v1/faces/verify \
  -F "image=@test_face.jpg" \
  -F "face_id=face_abc123"
```

## 📖 Contributing

When adding new endpoints:

1. **Define schema** in `schemas/request.py` or `schemas/response.py`
2. **Create endpoint** in `endpoints/` module
3. **Add route** in `routes.py`
4. **Document** with docstrings and examples
5. **Test** with pytest
6. **Update** this README

## 🔗 Dependencies

- FastAPI - Web framework
- Pydantic - Request/response validation
- python-jose - JWT handling
- starlette - HTTP utilities

---

**Last Updated:** 2025-11-12
