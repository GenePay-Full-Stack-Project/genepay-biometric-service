"""
Face Recognition Service
Handles face detection, encoding, and verification with liveness detection
"""
import face_recognition
import numpy as np
import cv2
from typing import Optional, Tuple, List, Dict
import logging
from app.config import settings
from app.services.liveness_detector import LivenessDetector

logger = logging.getLogger(__name__)


class FaceRecognitionService:
    """Main face recognition service with liveness detection"""
    
    def __init__(self):
        # Use balanced tolerance for real-world conditions across different locations/lighting
        # 0.60 provides good matching while maintaining security
        # Lower tolerance = stricter matching but better confidence scores
        self.tolerance = getattr(settings, 'FACE_RECOGNITION_TOLERANCE', 0.60)
        self.model = settings.FACE_ENCODING_MODEL
        self.liveness_detector = LivenessDetector(
            min_sharpness=settings.LIVENESS_MIN_SHARPNESS,
            min_brightness=settings.LIVENESS_MIN_BRIGHTNESS,
            max_brightness=settings.LIVENESS_MAX_BRIGHTNESS
        )
        logger.info(f"FaceRecognitionService initialized with tolerance={self.tolerance}, model={self.model}")
    
    def detect_and_encode_face(self, 
                               image: np.ndarray,
                               check_liveness: bool = True) -> Dict:
        """
        Detect face in image, extract encoding, and optionally check liveness
        
        Args:
            image: NumPy array of the image
            check_liveness: Whether to perform liveness detection
            
        Returns:
            Dict containing:
            - success: bool
            - encoding: List[float] or None
            - face_location: Tuple or None
            - liveness_result: Dict or None
            - error: str or None
        """
        try:
            # Validate image
            if image is None or image.size == 0:
                return {
                    'success': False,
                    'error': 'Invalid image data'
                }
            
            # Check image quality
            quality_check = self._check_image_quality(image)
            if not quality_check['valid']:
                return {
                    'success': False,
                    'error': quality_check['message']
                }
            
            # Convert BGR (OpenCV) to RGB — face_recognition/dlib requires RGB input
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # Detect faces using the configured model
            # For verification, HOG is much faster and usually sufficient
            face_locations = face_recognition.face_locations(
                rgb_image,
                model="hog",  # Always use HOG for speed (3-5x faster than CNN)
                number_of_times_to_upsample=1  # Reduce upsampling for speed
            )
            
            if len(face_locations) == 0:
                return {
                    'success': False,
                    'error': 'No face detected in image'
                }
            
            if len(face_locations) > 1:
                return {
                    'success': False,
                    'error': 'Multiple faces detected. Please ensure only one face is visible'
                }
            
            face_location = face_locations[0]
            
            # Normalize face region for consistent encoding across lighting conditions
            image = self._normalize_face_region(image, face_location)
            # Re-convert normalized BGR image to RGB for face_recognition library
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # Check face size
            top, right, bottom, left = face_location
            face_width = right - left
            face_height = bottom - top

            if face_width < settings.MIN_FACE_SIZE or face_height < settings.MIN_FACE_SIZE:
                return {
                    'success': False,
                    'error': f'Face is too small. Minimum size is {settings.MIN_FACE_SIZE}x{settings.MIN_FACE_SIZE} pixels'
                }

            # Extract face encoding using small model for speed
            # For enrollment, generate MULTIPLE encodings with different jitters to capture variations
            # For verification, use 1 jitter for speed (we'll compare against all stored encodings)
            if check_liveness:
                # ENROLLMENT: Generate multiple encodings with different variations
                # This captures the face in different representations for robust matching
                all_encodings = []

                # Get base encoding with high jitters
                encodings_1 = face_recognition.face_encodings(
                    rgb_image,
                    known_face_locations=[face_location],
                    model="small",
                    num_jitters=10
                )
                if encodings_1:
                    all_encodings.append(encodings_1[0])

                # Get encoding from slightly brightened image (RGB)
                bright_image = cv2.convertScaleAbs(rgb_image, alpha=1.2, beta=10)
                encodings_2 = face_recognition.face_encodings(
                    bright_image,
                    known_face_locations=[face_location],
                    model="small",
                    num_jitters=5
                )
                if encodings_2:
                    all_encodings.append(encodings_2[0])

                # Get encoding from slightly darkened image (RGB)
                dark_image = cv2.convertScaleAbs(rgb_image, alpha=0.8, beta=-10)
                encodings_3 = face_recognition.face_encodings(
                    dark_image,
                    known_face_locations=[face_location],
                    model="small",
                    num_jitters=5
                )
                if encodings_3:
                    all_encodings.append(encodings_3[0])
                
                if len(all_encodings) == 0:
                    return {
                        'success': False,
                        'error': 'Failed to generate face encodings'
                    }
                
                face_encoding = all_encodings  # Return list of encodings
            else:
                # VERIFICATION: Single encoding with 1 jitter for speed
                face_encodings = face_recognition.face_encodings(
                    rgb_image,
                    known_face_locations=[face_location],
                    model="small",
                    num_jitters=1
                )
                
                if len(face_encodings) == 0:
                    return {
                        'success': False,
                        'error': 'Failed to generate face encoding'
                    }
                
                face_encoding = face_encodings[0]  # Return single encoding
            
            # Perform liveness detection
            liveness_result = None
            if check_liveness and settings.ENABLE_LIVENESS_DETECTION:
                liveness_result = self.liveness_detector.detect(image)
                
                if not liveness_result['is_live']:
                    return {
                        'success': False,
                        'error': liveness_result.get('message', 'Liveness check failed'),
                        'liveness_result': liveness_result
                    }
            
            # Convert encoding(s) to list format
            if check_liveness:
                # Multiple encodings for enrollment
                encoding_data = [enc.tolist() for enc in face_encoding]
            else:
                # Single encoding for verification
                encoding_data = face_encoding.tolist()
            
            return {
                'success': True,
                'encoding': encoding_data,
                'face_location': face_location,
                'liveness_result': liveness_result,
                'quality_score': quality_check['score']
            }
            
        except Exception as e:
            logger.error(f"Error in detect_and_encode_face: {e}")
            return {
                'success': False,
                'error': f'Face processing error: {str(e)}'
            }
    
    def verify_face(self, 
                    face_encoding: List[float], 
                    stored_encodings: List[List[float]],
                    tolerance: Optional[float] = None) -> Dict:
        """
        Verify face encoding against multiple stored encodings
        Returns best match from all stored variations
        
        Args:
            face_encoding: Single encoding from verification attempt
            stored_encodings: List of stored encodings from database (multiple variations)
            tolerance: Optional custom tolerance (default uses settings)
            
        Returns:
            Dict with verification result (best match)
        """
        try:
            if tolerance is None:
                tolerance = self.tolerance
            
            # Handle both old format (single encoding) and new format (multiple encodings)
            # Check if stored_encodings is a single encoding (list of floats) or multiple (list of lists)
            if stored_encodings and isinstance(stored_encodings[0], (int, float)):
                # Old format: single encoding - convert to list of encodings
                stored_encodings = [stored_encodings]
            
            # Convert to numpy array
            encoding1 = np.array(face_encoding)
            
            # Compare against ALL stored encodings and get best match
            best_match = False
            best_confidence = 0.0
            best_distance = float('inf')
            
            for stored_enc in stored_encodings:
                encoding2 = np.array(stored_enc)
                
                # Calculate face distance (lower is better)
                distance = face_recognition.face_distance([encoding2], encoding1)[0]
                
                # Check if this encoding matches
                matches = distance <= tolerance
                
                # Calculate confidence (inverse of distance, normalized)
                confidence = 1.0 - min(distance / tolerance, 1.0)
                
                # Keep track of best match
                if matches and confidence > best_confidence:
                    best_match = True
                    best_confidence = confidence
                    best_distance = distance
            
            return {
                'match': bool(best_match),
                'confidence': float(best_confidence),
                'distance': float(best_distance),
                'tolerance': tolerance,
                'encodings_checked': len(stored_encodings)
            }
            
        except Exception as e:
            logger.error(f"Error in verify_face: {e}")
            return {
                'match': False,
                'confidence': 0.0,
                'error': str(e)
            }
    
    def compare_multiple_faces(self, 
                               face_encoding: List[float],
                               stored_encodings: List[List[float]],
                               tolerance: Optional[float] = None) -> List[Dict]:
        """
        Compare a face encoding against multiple stored encodings
        
        Returns:
            List of match results sorted by confidence
        """
        try:
            if tolerance is None:
                tolerance = self.tolerance
            
            encoding = np.array(face_encoding)
            stored = [np.array(enc) for enc in stored_encodings]
            
            # Calculate distances
            distances = face_recognition.face_distance(stored, encoding)
            
            # Generate results
            results = []
            for i, distance in enumerate(distances):
                matches = distance <= tolerance
                confidence = 1.0 - min(distance / tolerance, 1.0)
                
                results.append({
                    'index': i,
                    'match': bool(matches),
                    'confidence': float(confidence),
                    'distance': float(distance)
                })
            
            # Sort by confidence (descending)
            results.sort(key=lambda x: x['confidence'], reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in compare_multiple_faces: {e}")
            return []
    
    def _check_image_quality(self, image: np.ndarray) -> Dict:
        """
        Check if image meets minimum quality requirements
        
        Returns:
            Dict with validation result and quality score
        """
        try:
            # Check dimensions
            if len(image.shape) < 2:
                return {
                    'valid': False,
                    'message': 'Invalid image dimensions',
                    'score': 0.0
                }
            
            height, width = image.shape[:2]
            
            # Check minimum size - very lenient for real-world conditions
            if width < 150 or height < 150:
                return {
                    'valid': False,
                    'message': 'Image resolution too low. Minimum 150x150 pixels required',
                    'score': 0.3
                }
            
            # Check if image is too dark or too bright
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            avg_brightness = np.mean(gray)
            
            # Very lenient brightness thresholds - accept almost any reasonable lighting
            if avg_brightness < 10:  # Extremely dark
                return {
                    'valid': False,
                    'message': 'Image is too dark. Please improve lighting',
                    'score': 0.4
                }
            
            if avg_brightness > 245:  # Extremely bright
                return {
                    'valid': False,
                    'message': 'Image is too bright. Please reduce lighting',
                    'score': 0.4
                }
            
            # Calculate quality score based on sharpness
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            quality_score = min(laplacian_var / 500.0, 1.0)
            
            # Very lenient sharpness check - accept almost any image where face can be detected
            if laplacian_var < 20:  # Only reject extremely blurry images
                logger.warning(f"Very low sharpness detected: {laplacian_var:.2f}")
                quality_score = max(quality_score, 0.2)  # Minimum acceptable score
            
            return {
                'valid': True,
                'message': 'Image quality acceptable',
                'score': quality_score
            }
            
        except Exception as e:
            logger.error(f"Error checking image quality: {e}")
            return {
                'valid': False,
                'message': f'Quality check error: {str(e)}',
                'score': 0.0
            }
    
    def _normalize_face_region(self, 
                               image: np.ndarray, 
                               face_location: Tuple[int, int, int, int]) -> np.ndarray:
        """
        Normalize face region to reduce lighting variations
        Uses histogram equalization for consistent encoding
        
        Args:
            image: Full image
            face_location: (top, right, bottom, left) tuple
            
        Returns:
            Normalized image
        """
        try:
            # Convert to grayscale if needed for analysis
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            # This normalizes lighting while preserving local details
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            normalized_gray = clahe.apply(gray)
            
            # If color image, apply normalization to luminance channel only
            if len(image.shape) == 3:
                # Convert to LAB color space
                lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                
                # Apply CLAHE to L channel
                l = clahe.apply(l)
                
                # Merge and convert back
                normalized_lab = cv2.merge([l, a, b])
                normalized_image = cv2.cvtColor(normalized_lab, cv2.COLOR_LAB2BGR)
                
                return normalized_image
            else:
                return normalized_gray
            
        except Exception as e:
            logger.warning(f"Face normalization failed, using original: {e}")
            return image
    
    def extract_face_region(self, 
                           image: np.ndarray, 
                           face_location: Tuple[int, int, int, int],
                           padding: int = 20) -> Optional[np.ndarray]:
        """
        Extract face region from image with padding
        
        Args:
            image: Full image
            face_location: (top, right, bottom, left) tuple
            padding: Padding around face in pixels
            
        Returns:
            Cropped face image or None
        """
        try:
            top, right, bottom, left = face_location
            height, width = image.shape[:2]
            
            # Apply padding with bounds checking
            top = max(0, top - padding)
            right = min(width, right + padding)
            bottom = min(height, bottom + padding)
            left = max(0, left - padding)
            
            # Crop face region
            face_image = image[top:bottom, left:right]
            
            return face_image
            
        except Exception as e:
            logger.error(f"Error extracting face region: {e}")
            return None
