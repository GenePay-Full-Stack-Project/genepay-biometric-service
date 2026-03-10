"""
Image Processing Utilities
"""
import cv2
import numpy as np
from PIL import Image
import base64
import io
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def base64_to_image(base64_string: str) -> Optional[np.ndarray]:
    """
    Convert base64 string to OpenCV image (NumPy array)
    Handles EXIF orientation automatically
    
    Args:
        base64_string: Base64 encoded image string
        
    Returns:
        NumPy array or None if conversion fails
    """
    try:
        # Remove data URL prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        # Decode base64
        image_bytes = base64.b64decode(base64_string)
        
        # Convert to PIL Image
        pil_image = Image.open(io.BytesIO(image_bytes))
        
        # Handle EXIF orientation
        try:
            # Get EXIF data
            exif = pil_image._getexif()
            if exif is not None:
                # EXIF orientation tag is 274
                orientation = exif.get(274, 1)
                
                # Apply rotation based on orientation
                if orientation == 2:
                    pil_image = pil_image.transpose(Image.FLIP_LEFT_RIGHT)
                elif orientation == 3:
                    pil_image = pil_image.rotate(180, expand=True)
                elif orientation == 4:
                    pil_image = pil_image.rotate(180, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
                elif orientation == 5:
                    pil_image = pil_image.rotate(-90, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
                elif orientation == 6:
                    pil_image = pil_image.rotate(-90, expand=True)
                elif orientation == 7:
                    pil_image = pil_image.rotate(90, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
                elif orientation == 8:
                    pil_image = pil_image.rotate(90, expand=True)
                
                logger.debug(f"Applied EXIF orientation correction: {orientation}")
        except (AttributeError, KeyError, IndexError) as e:
            # No EXIF data or orientation tag
            logger.debug(f"No EXIF orientation data: {e}")
        
        # Convert to RGB if necessary
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        # Convert to NumPy array
        image_array = np.array(pil_image)
        
        # Convert RGB to BGR for OpenCV
        image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        
        return image_bgr
        
    except Exception as e:
        logger.error(f"Error converting base64 to image: {e}")
        return None


def image_to_base64(image: np.ndarray, format: str = 'JPEG') -> Optional[str]:
    """
    Convert OpenCV image to base64 string
    
    Args:
        image: NumPy array (OpenCV image)
        format: Image format (JPEG, PNG)
        
    Returns:
        Base64 encoded string or None
    """
    try:
        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(image_rgb)
        
        # Save to bytes buffer
        buffer = io.BytesIO()
        pil_image.save(buffer, format=format)
        buffer.seek(0)
        
        # Encode to base64
        base64_string = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return f"data:image/{format.lower()};base64,{base64_string}"
        
    except Exception as e:
        logger.error(f"Error converting image to base64: {e}")
        return None


def resize_image(image: np.ndarray, 
                max_width: int = 1024, 
                max_height: int = 1024) -> np.ndarray:
    """
    Resize image while maintaining aspect ratio
    Optimizes large images for faster processing
    
    Args:
        image: Input image
        max_width: Maximum width
        max_height: Maximum height
        
    Returns:
        Resized image
    """
    try:
        height, width = image.shape[:2]
        
        # Calculate scaling factor
        scale = min(max_width / width, max_height / height, 1.0)
        
        if scale < 1.0:
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            resized = cv2.resize(image, (new_width, new_height), 
                               interpolation=cv2.INTER_AREA)
            logger.debug(f"Resized image from {width}x{height} to {new_width}x{new_height}")
            return resized
        
        return image
        
    except Exception as e:
        logger.error(f"Error resizing image: {e}")
        return image


def optimize_for_processing(image: np.ndarray, 
                           max_dimension: int = 800) -> np.ndarray:
    """
    Optimize image for faster face detection and processing
    Reduces size while maintaining face detection accuracy
    
    Args:
        image: Input image
        max_dimension: Maximum width or height (smaller = faster)
        
    Returns:
        Optimized image
    """
    try:
        height, width = image.shape[:2]
        
        # Only resize if image is larger than threshold
        if max(height, width) > max_dimension:
            scale = max_dimension / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            optimized = cv2.resize(image, (new_width, new_height), 
                                 interpolation=cv2.INTER_AREA)
            logger.info(f"Optimized image from {width}x{height} to {new_width}x{new_height} for faster processing")
            return optimized
        
        return image
        
    except Exception as e:
        logger.error(f"Error optimizing image: {e}")
        return image


def enhance_image(image: np.ndarray) -> np.ndarray:
    """
    Enhance image quality for better face recognition
    
    Args:
        image: Input image
        
    Returns:
        Enhanced image
    """
    try:
        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        
        # Split channels
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_enhanced = clahe.apply(l)
        
        # Merge channels
        enhanced_lab = cv2.merge([l_enhanced, a, b])
        
        # Convert back to BGR
        enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        
        # Apply slight sharpening
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        # Blend original and sharpened (50/50)
        result = cv2.addWeighted(enhanced, 0.7, sharpened, 0.3, 0)
        
        return result
        
    except Exception as e:
        logger.error(f"Error enhancing image: {e}")
        return image


def validate_image_size(image_bytes: bytes, max_size_mb: int = 5) -> Tuple[bool, str]:
    """
    Validate image file size
    
    Args:
        image_bytes: Image data in bytes
        max_size_mb: Maximum allowed size in MB
        
    Returns:
        Tuple of (is_valid, message)
    """
    size_mb = len(image_bytes) / (1024 * 1024)
    
    if size_mb > max_size_mb:
        return False, f"Image size ({size_mb:.2f}MB) exceeds maximum allowed size ({max_size_mb}MB)"
    
    return True, "Image size is valid"


def draw_face_box(image: np.ndarray, 
                 face_location: Tuple[int, int, int, int],
                 label: str = "",
                 confidence: Optional[float] = None) -> np.ndarray:
    """
    Draw bounding box around detected face
    
    Args:
        image: Input image
        face_location: (top, right, bottom, left)
        label: Label text to display
        confidence: Confidence score to display
        
    Returns:
        Image with drawn box
    """
    try:
        result = image.copy()
        top, right, bottom, left = face_location
        
        # Draw rectangle
        cv2.rectangle(result, (left, top), (right, bottom), (0, 255, 0), 2)
        
        # Draw label
        if label or confidence is not None:
            text = label
            if confidence is not None:
                text += f" ({confidence:.2%})"
            
            # Calculate text size
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            thickness = 2
            (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)
            
            # Draw background rectangle for text
            cv2.rectangle(result, 
                         (left, top - text_height - 10), 
                         (left + text_width, top), 
                         (0, 255, 0), -1)
            
            # Draw text
            cv2.putText(result, text, (left, top - 5), 
                       font, font_scale, (0, 0, 0), thickness)
        
        return result
        
    except Exception as e:
        logger.error(f"Error drawing face box: {e}")
        return image


def normalize_image(image: np.ndarray) -> np.ndarray:
    """
    Normalize image for consistent processing
    
    Args:
        image: Input image
        
    Returns:
        Normalized image
    """
    try:
        # Convert to float32
        normalized = image.astype(np.float32)
        
        # Normalize to [0, 1]
        normalized = normalized / 255.0
        
        return normalized
        
    except Exception as e:
        logger.error(f"Error normalizing image: {e}")
        return image


def anonymize_face_image(image: np.ndarray, 
                        face_location: Tuple[int, int, int, int],
                        blur_strength: int = 25) -> np.ndarray:
    """
    Anonymize face image by heavily blurring facial features
    while keeping the overall structure visible for audit purposes
    
    Args:
        image: Original image
        face_location: (top, right, bottom, left) of face
        blur_strength: Blur kernel size (must be odd, higher = more blur)
        
    Returns:
        Anonymized image with blurred face
    """
    try:
        result = image.copy()
        top, right, bottom, left = face_location
        
        # Extract face region
        face_region = result[top:bottom, left:right]
        
        # Apply strong Gaussian blur to face region
        if blur_strength % 2 == 0:
            blur_strength += 1  # Must be odd
        
        blurred_face = cv2.GaussianBlur(face_region, (blur_strength, blur_strength), 0)
        
        # Apply additional pixelation for extra anonymization
        # Downscale and upscale to create pixelated effect
        small = cv2.resize(blurred_face, (16, 16), interpolation=cv2.INTER_LINEAR)
        pixelated = cv2.resize(small, (right - left, bottom - top), 
                              interpolation=cv2.INTER_NEAREST)
        
        # Replace face region with anonymized version
        result[top:bottom, left:right] = pixelated
        
        logger.info("Face image anonymized successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error anonymizing face: {e}")
        # Return heavily blurred image as fallback
        return cv2.GaussianBlur(image, (99, 99), 0)


def prepare_image_for_upload(image: np.ndarray,
                            face_location: Tuple[int, int, int, int],
                            max_size: int = 400) -> bytes:
    """
    Prepare image for S3 upload: anonymize, resize, and compress
    
    Args:
        image: Original image
        face_location: Face location for anonymization
        max_size: Maximum dimension (width/height) for resized image
        
    Returns:
        Compressed JPEG bytes of anonymized image
    """
    try:
        # Anonymize the face
        anonymized = anonymize_face_image(image, face_location)
        
        # Resize to reduce storage size
        height, width = anonymized.shape[:2]
        scale = min(max_size / width, max_size / height, 1.0)
        
        if scale < 1.0:
            new_width = int(width * scale)
            new_height = int(height * scale)
            anonymized = cv2.resize(anonymized, (new_width, new_height), 
                                   interpolation=cv2.INTER_AREA)
        
        # Compress with moderate quality (smaller file size)
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, 70]
        _, buffer = cv2.imencode('.jpg', anonymized, encode_params)
        
        return buffer.tobytes()
        
    except Exception as e:
        logger.error(f"Error preparing image for upload: {e}")
        # Return minimal placeholder
        placeholder = np.zeros((100, 100, 3), dtype=np.uint8)
        _, buffer = cv2.imencode('.jpg', placeholder)
        return buffer.tobytes()
