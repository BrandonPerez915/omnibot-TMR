"""
Sistema centralizado de logging para OmniBot Computer Vision.

Proporciona funciones para inicializar y obtener loggers consistentes
en toda la aplicación, optimize para Jetson Orin Nano.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Final

PROJECT_PATH: Final[Path] = Path(__file__).parent
LOGS_PATH: Final[Path] = PROJECT_PATH / "logs"


class LoggerManager:
    """Gestor centralizado de loggers."""

    _initialized: bool = False
    _default_level: int = logging.INFO
    _default_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @classmethod
    def initialize(
        cls,
        level: int = logging.INFO,
        log_file: Optional[Path] = None,
        format_str: Optional[str] = None,
        max_bytes: int = 10485760,  # 10MB
        backup_count: int = 5,
    ) -> None:
        """
        Inicializa el sistema de logging centralizado.

        Args:
            level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Ruta del archivo de log. Si es None, no se guarda archivo.
            format_str: Formato de los mensajes de log
            max_bytes: Tamaño máximo del archivo de log antes de rotar
            backup_count: Número de archivos de backup a mantener
        """
        if cls._initialized:
            return

        if format_str:
            cls._default_format = format_str

        cls._default_level = level

        # Configurar root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(cls._default_format)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        # Handler para archivo (si se especifica)
        if log_file:
            log_file = Path(log_file)
            log_file.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count
            )
            file_handler.setLevel(level)
            file_formatter = logging.Formatter(cls._default_format)
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)

        cls._initialized = True

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Obtiene un logger con el nombre especificado.

        Args:
            name: Nombre del logger (usualmente __name__)

        Returns:
            logging.Logger: Logger configurado
        """
        return logging.getLogger(name)


def get_logger(name: str) -> logging.Logger:
    """
    Función de conveniencia para obtener un logger.

    Args:
        name: Nombre del logger (usualmente __name__)

    Returns:
        logging.Logger: Logger configurado
    """
    return LoggerManager.get_logger(name)


# Inicializar logging por defecto
LoggerManager.initialize(level=logging.INFO, log_file=LOGS_DIR / "omnibot.log")
