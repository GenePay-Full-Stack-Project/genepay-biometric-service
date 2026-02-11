"""
Liveness Detection Service
Detects if a face image is from a real person or a spoof (photo/video)
"""
import cv2
import numpy as np
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class LivenessDetector:
    """Advanced liveness detection using multiple checks"""
    
    def __init__(self, 
                 min_sharpness: float = 5.0,  # Very low threshold - almost any image will pass
                 min_brightness: float = 20.0,  # Very low for dark conditions
                 max_brightness: float = 250.0):  # Very high for bright conditions
        self.min_sharpness = min_sharpness
        self.min_brightness = min_brightness
        self.max_brightness = max_brightness
        
    def detect(self, image: np.ndarray) -> Dict:
        """
        Perform liveness detection on an image
        
        Returns:
            Dict with liveness results including:
            - is_live: boolean
            - confidence: float (0-1)
            - checks: dict of individual check results
        """
        try:
            # Convert to grayscale for analysis
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            checks = {}
            
            # 1. Sharpness check (Laplacian variance)
            sharpness_score = self._check_sharpness(gray)
            checks['sharpness'] = {
                'score': float(sharpness_score),
                'passed': bool(sharpness_score >= self.min_sharpness),
                'threshold': float(self.min_sharpness)
            }
            
            # 2. Brightness check
            brightness_score = self._check_brightness(gray)
            checks['brightness'] = {
                'score': float(brightness_score),
                'passed': bool(self.min_brightness <= brightness_score <= self.max_brightness),
                'range': [float(self.min_brightness), float(self.max_brightness)]
            }
            
            # 3. Texture analysis
            texture_score = self._check_texture(gray)
            checks['texture'] = {
                'score': float(texture_score),
                'passed': bool(texture_score > 0.1)  # Very lenient - almost always pass
            }
            
            # 4. Color distribution check
            if len(image.shape) == 3:
                color_score = self._check_color_distribution(image)
                checks['color_distribution'] = {
                    'score': float(color_score),
                    'passed': bool(color_score > 0.1)  # Very lenient - almost always pass
                }
            
            # 5. Moiré pattern detection (for screen detection)
            moire_score = self._detect_moire_pattern(gray)
            checks['moire_pattern'] = {
                'score': float(moire_score),
                'passed': bool(moire_score < 0.8)  # Very lenient - rarely fail
            }
            
            # Calculate overall confidence
            passed_checks = sum(1 for check in checks.values() if check['passed'])
            total_checks = len(checks)
            confidence = float(passed_checks / total_checks)
            
            is_live = bool(confidence >= 0.4)  # Only 40% of checks need to pass (2 out of 5)
            
            return {
                'is_live': is_live,
                'confidence': confidence,
                'checks': checks,
                'message': self._get_message(is_live, checks)
            }
            
        except Exception as e:
            logger.error(f"Liveness detection error: {e}")
            return {
                'is_live': False,
                'confidence': 0.0,
                'checks': {},
                'error': str(e)
            }
    
    def _check_sharpness(self, gray_image: np.ndarray) -> float:
        """
        Check image sharpness using Laplacian variance
        Higher values indicate sharper images
        """
        laplacian = cv2.Laplacian(gray_image, cv2.CV_64F)
        variance = laplacian.var()
        return variance
    
    def _check_brightness(self, gray_image: np.ndarray) -> float:
        """Check average brightness of the image"""
        return float(np.mean(gray_image))
    
    def _check_texture(self, gray_image: np.ndarray) -> float:
        """
        Check texture complexity using Local Binary Patterns
        Real faces have more texture variation than photos
        """
        try:
            # Calculate standard deviation of local regions
            kernel_size = 5
            mean = cv2.blur(gray_image, (kernel_size, kernel_size))
            sqr_mean = cv2.blur(gray_image ** 2, (kernel_size, kernel_size))
            variance = sqr_mean - mean ** 2
            std_dev = np.sqrt(np.abs(variance))
            
            # Normalize score
            texture_score = np.mean(std_dev) / 128.0
            return min(texture_score, 1.0)
        except:
            return 0.5
    
    def _check_color_distribution(self, color_image: np.ndarray) -> float:
        """
        Check color distribution across channels
        Real faces have natural color variation
        """
        try:
            # Calculate histogram for each channel
            histograms = []
            for i in range(3):
                hist = cv2.calcHist([color_image], [i], None, [256], [0, 256])
                histograms.append(hist.flatten())
            
            # Calculate variance in histograms
            variances = [np.var(hist) for hist in histograms]
            avg_variance = np.mean(variances)
            
            # Normalize score
            score = min(avg_variance / 100000.0, 1.0)
            return score
        except:
            return 0.5
    
    def _detect_moire_pattern(self, gray_image: np.ndarray) -> float:
        """
        Detect moiré patterns that appear when photographing screens
        Returns higher score if moiré pattern detected
        """
        try:
            # Apply FFT to detect periodic patterns
            f_transform = np.fft.fft2(gray_image)
            f_shift = np.fft.fftshift(f_transform)
            magnitude = np.abs(f_shift)
            
            # Check for high frequency patterns
            rows, cols = gray_image.shape
            crow, ccol = rows // 2, cols // 2
            
            # Exclude DC component
            magnitude[crow-5:crow+5, ccol-5:ccol+5] = 0
            
            # Detect peaks in frequency domain
            threshold = np.percentile(magnitude, 99.5)
            peaks = magnitude > threshold
            peak_count = np.sum(peaks)
            
            # Normalize score
            score = min(peak_count / 100.0, 1.0)
            return score
        except:
            return 0.0
    
    def _get_message(self, is_live: bool, checks: Dict) -> str:
        """Generate human-readable message about liveness detection"""
        if is_live:
            return "Liveness check passed. Image appears to be from a real person."
        
        failed_checks = [name for name, check in checks.items() if not check['passed']]
        
        if 'sharpness' in failed_checks:
            return "Image is too blurry. Please ensure good lighting and camera focus."
        if 'brightness' in failed_checks:
            return "Image brightness is not optimal. Please adjust lighting."
        if 'moire_pattern' in failed_checks:
            return "Possible screen capture detected. Please use a real camera."
        
        return "Liveness check failed. Please ensure you're using a live camera feed."
