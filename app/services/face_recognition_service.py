"""
Face Recognition Service
Core face detection and matching logic
"""

import face_recognition
import numpy as np
from typing import Optional, List
from PIL import Image
import io


class FaceRecognitionService:
    """Service for face detection, encoding, and matching"""
    
    def __init__(self, model: str = "large", threshold: float = 0.6):
        """
        Initialize face recognition service
        
        Args:
            model: Recognition model ("large" or "small")
            threshold: Matching threshold (lower = stricter)
        """
        self.model = model
        self.threshold = threshold
    
    async def detect_face(self, image_bytes: bytes) -> bool:
        """
        Detect if a face exists in the image
        
        Args:
            image_bytes: Image file bytes
            
        Returns:
            True if face detected, False otherwise
        """
        try:
            # Load image
            image = face_recognition.load_image_file(io.BytesIO(image_bytes))
            
            # Detect faces
            face_locations = face_recognition.face_locations(image)
            
            return len(face_locations) > 0
        except Exception as e:
            print(f"Error detecting face: {str(e)}")
            return False
    
    async def generate_face_encoding(self, image_bytes: bytes) -> Optional[List[float]]:
        """
        Generate face encoding (128-dimensional vector)
        
        Args:
            image_bytes: Image file bytes
            
        Returns:
            List of 128 float values representing face encoding, or None if failed
        """
        try:
            # Load image
            image = face_recognition.load_image_file(io.BytesIO(image_bytes))
            
            # Generate encodings
            encodings = face_recognition.face_encodings(image, model=self.model)
            
            if len(encodings) == 0:
                return None
            
            # Return first face encoding as list
            return encodings[0].tolist()
        except Exception as e:
            print(f"Error generating face encoding: {str(e)}")
            return None
    
    async def compare_faces(
        self,
        known_encoding: List[float],
        test_encoding: List[float]
    ) -> tuple[bool, float]:
        """
        Compare two face encodings
        
        Args:
            known_encoding: Stored face encoding
            test_encoding: Test face encoding
            
        Returns:
            Tuple of (match: bool, confidence: float)
        """
        try:
            # Convert to numpy arrays
            known = np.array(known_encoding)
            test = np.array(test_encoding)
            
            # Calculate face distance (lower = more similar)
            distance = face_recognition.face_distance([known], test)[0]
            
            # Convert distance to confidence (0-1, higher = more confident)
            confidence = 1 - distance
            
            # Check if match
            match = distance <= self.threshold
            
            return match, float(confidence)
        except Exception as e:
            print(f"Error comparing faces: {str(e)}")
            return False, 0.0
    
    async def validate_image(self, image_bytes: bytes) -> tuple[bool, str]:
        """
        Validate image quality and format
        
        Args:
            image_bytes: Image file bytes
            
        Returns:
            Tuple of (valid: bool, message: str)
        """
        try:
            # Open image with PIL
            image = Image.open(io.BytesIO(image_bytes))
            
            # Check format
            if image.format not in ['JPEG', 'PNG']:
                return False, "Invalid image format. Use JPEG or PNG."
            
            # Check size
            width, height = image.size
            if width < 200 or height < 200:
                return False, "Image too small. Minimum 200x200 pixels."
            
            if width > 4000 or height > 4000:
                return False, "Image too large. Maximum 4000x4000 pixels."
            
            return True, "Image valid"
        except Exception as e:
            return False, f"Invalid image: {str(e)}"
