"""
BioPay Biometric Service - Application Package

Main application entry point and package initialization.
"""

__version__ = "1.0.0"
__author__ = "BioPay Team"
__description__ = "Face recognition and verification service for BioPay payment system"

from .main import app

__all__ = ["app"]
