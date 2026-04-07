"""
Constantes del proyecto OmniBot Computer Vision.

Este módulo centraliza todas las constantes utilizadas en el proyecto
para facilitar mantenimiento y evitar hardcoding en el código.
"""

from pathlib import Path
from typing import Final

# Rutas
PROJECT_PATH: Final[Path] = Path(__file__).parent.parent
MODEL_DIR: Final[Path] = PROJECT_PATH / "model"
SAVE_DIR: Final[Path] = PROJECT_PATH / "data"
LOGS_DIR: Final[Path] = PROJECT_PATH / "logs"

# Crear directorios si no existen
LOGS_DIR.mkdir(exist_ok=True)
SAVE_DIR.mkdir(exist_ok=True)


# Comandos SPI para ESP32
class SPICommands:
    """Comandos SPI válidos para comunicación con ESP32."""

    START: Final[str] = "E"  # Iniciar
    STRAIGHT: Final[str] = "F"  # Avanzar recto
    STOP: Final[str] = "O"  # Detener


# Estados de granos
class BeanStates:
    """Estados de madurez de los granos."""

    UNRIPE: Final[int] = 0
    RIPE: Final[int] = 1
    OVERRIPE: Final[int] = 2

    # Nombres legibles
    NAMES: Final[dict] = {UNRIPE: "Inmaduro", RIPE: "Maduro", OVERRIPE: "Sobremaduro"}


# Tamaños de imagen (para optimización en Jetson Orin Nano)
class ImageSizes:
    """Tamaños estándar de imágenes."""

    IMX219_WIDTH: Final[tuple] = 1280
    IMX219_HEIGHT: Final[tuple] = 720
    WEBCAM_WIDTH: Final[tuple] = 640
    WEBCAM_HEIGHT: Final[tuple] = 480
    DISPLAY_WIDTH: Final[tuple] = 640
    DISPLAY_HEIGHT: Final[tuple] = 480


class CameraConfig:
    """Configuración de cámaras."""

    FRAME_RATE: Final[int] = 30
    # Métodos de flip para cámaras CSI (IMX219)
    FLIP_0: Final[int] = 0
    FLIP_90: Final[int] = 1
    FLIP_180: Final[int] = 2
    FLIP_270: Final[int] = 3


# Códigos de error
class ErrorCodes:
    """Códigos de error estándar."""

    CAMERA_NOT_FOUND: Final[int] = 1
    MODEL_NOT_FOUND: Final[int] = 2
    SPI_ERROR: Final[int] = 3
    FRAME_ERROR: Final[int] = 4
    INVALID_CONFIG: Final[int] = 5
