"""
OmniBot Computer Vision
Módulo principal
"""

import entities
import utils

__version__ = "2.0.0"
__author__ = "Brandon Pérez"
__description__ = "Sistema de visión para OmniBot en Jetson Orin Nano"
__all__ = ["entities", "utils"]

from logger import get_logger

logger = get_logger(__name__)
logger.debug(f"OmniBot CV v{__version__} cargado")
