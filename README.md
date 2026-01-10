# 🔐 Biometric Service API

**Basic FastAPI Application for Face Recognition & Verification**

## 📋 Overview

A simple FastAPI application providing biometric endpoints for face registration and verification.

## 🚀 Features

- **Face Registration**: Register user faces
- **Face Verification**: Verify user faces
- **RESTful API**: Clean API with automatic Swagger documentation
- **Basic Structure**: Simple, easy-to-understand codebase

## 🛠️ Technology Stack

- **Framework**: FastAPI 0.115.0
- **Language**: Python 3.11+

## 📦 Installation

### Prerequisites

- Python 3.11 or higher

### Setup Steps

1. **Navigate to the project directory**
```bash
cd genepay-biometric-service
```

2. **Create virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

## 🏃 Running the Service

### Development Mode
```bash
# With auto-reload
uvicorn app.main:app --reload --port 8001

# Or using Python
python app/main.py
```

## 📚 API Documentation

Once running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

## 🔌 API Endpoints

### Health Check
```http
GET /
GET /health
```

### Face Registration
```http
POST /register
Content-Type: multipart/form-data

Parameters:
- user_id: string
- face_image: file (JPEG/PNG image)
```

### Face Verification
```http
POST /verify
Content-Type: multipart/form-data

Parameters:
- user_id: string
- face_image: file (JPEG/PNG image)
```

### Get User Biometric Data
```http
GET /user/{user_id}
```

### Delete User Biometric Data
```http
DELETE /user/{user_id}
```

## 📁 Project Structure

```
genepay-biometric-service/
├── app/
│   ├── __init__.py
│   └── main.py           # FastAPI application with all endpoints
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
└── README.md            # This file
```

## 🧪 Testing

```bash
# Test health endpoint
curl http://localhost:8001/health

# Test face registration
curl -X POST "http://localhost:8001/register" \
  -F "user_id=user123" \
  -F "face_image=@path/to/face.jpg"
```

## 📞 Support

For issues and questions, create a GitHub issue.

## 📄 License

All rights reserved

---

**Basic FastAPI Starter**
