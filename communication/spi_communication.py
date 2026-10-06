"""
Módulo de comunicación SPI con ESP32.

Proporciona funciones para enviar comandos al microcontrolador ESP32
a través del protocolo SPI.
"""

import spidev
import time

from logger import get_logger
from constants import SPICommands

logger = get_logger(__name__)


class SPIManager:
    """Gestor de comunicación SPI con ESP32."""

    def __init__(
        self, port: int = 0, device: int = 0, max_speed_hz: int = 1000000, mode: int = 0
    ) -> None:
        """
        Inicializa el gestor SPI.

        Args:
            port: Puerto SPI (0 o 1)
            device: Dispositivo chip select
            max_speed_hz: Velocidad máxima en Hz
            mode: Modo SPI (0, 1, 2, o 3)

        Raises:
            RuntimeError: Si no se puede inicializar el bus SPI
        """
        try:
            self.spi = spidev.SpiDev()
            self.spi.open(port, device)
            self.spi.max_speed_hz = max_speed_hz
            self.spi.mode = mode
            logger.info(
                f"Bus SPI inicializado: puerto={port}, "
                f"dispositivo={device}, velocidad={max_speed_hz}Hz"
            )
        except Exception as e:
            logger.error(f"Error al inicializar SPI: {e}")
            raise RuntimeError(f"No se pudo inicializar el bus SPI: {e}")

    def send_command(self, command: str, timeout: float = 1.0, retry: int = 1) -> bool:
        """
        Envía un comando a la ESP32 sobre SPI.

        Nota: Se envían exactamente 4 bytes (comando + 3 ceros)
        para evitar bloqueos del DMA en la ESP32.

        Args:
            command: Comando a enviar (1 carácter)
            timeout: Tiempo máximo de espera en segundos
            retry: Número de intentos en caso de fallo

        Returns:
            bool: True si el envío fue exitoso, False en caso contrario

        Raises:
            ValueError: Si el comando no es válido
        """
        if not command or len(command) != 1:
            logger.warning(f"Comando inválido: '{command}'")
            raise ValueError("El comando debe ser un único carácter")

        cmd_byte = ord(command[0])
        payload = [cmd_byte, 0, 0, 0]  # 4 bytes: comando + padding

        for attempt in range(retry):
            try:
                self.spi.xfer2(payload)
                logger.debug(f"Comando enviado: '{command}' (intento {attempt + 1})")
                return True
            except Exception as e:
                logger.warning(
                    f"Error en intento {attempt + 1} de enviar '{command}': {e}"
                )
                if attempt < retry - 1:
                    time.sleep(timeout / retry)

        logger.error(f"Falló al enviar comando '{command}' después de {retry} intentos")
        return False
    
    def wait_for_response(self, timeout: float = 1.0) -> bool:
        """
        Espera una respuesta específica de la ESP32.

        Args:
            expected_response: Respuesta esperada en bytes
            timeout: Tiempo máximo de espera en segundos

        Returns:
            bool: True si se recibió la respuesta esperada, False en caso contrario
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = self.spi.readbytes(4)  # Leer 4 bytes de respuesta
                if bytes(response) == bytes(SPICommands.ESP_OK, 'utf-8'):
                    logger.debug(f"Respuesta recibida: {response}")
                    return True
            except Exception as e:
                logger.warning(f"Error al leer respuesta SPI: {e}")
                time.sleep(0.1)

        logger.error(f"No se recibió la respuesta esperada '{SPICommands.ESP_OK}' dentro del timeout")
        return False

    def close(self) -> None:
        """Cierra la conexión SPI."""
        try:
            if self.spi:
                self.spi.close()
                logger.info("Conexión SPI cerrada")
        except Exception as e:
            logger.error(f"Error al cerrar SPI: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
