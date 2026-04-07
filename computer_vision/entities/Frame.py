"""
Clase Frame para procesamiento de imágenes con GPU opcional.

Proporciona una abstracción sobre OpenCV que permite usar GPU CUDA
en Jetson Orin Nano para operaciones de procesamiento de imágenes.
"""

from typing import Tuple, Union, Optional, Any
import cv2 as cv
import numpy as np

from logger import get_logger

logger = get_logger(__name__)


class Frame:
    """
    Envoltura de imagen con soporte opcional para GPU CUDA.

    Proporciona métodos uniformes para trabajar con imágenes en CPU o GPU,
    optimizado para Jetson Orin Nano.

    Atributos:
        device: "cpu" o "gpu"
        image: cv.UMat (CPU) o cv.cuda_GpuMat (GPU)
    """

    def __init__(self, frame: np.ndarray, device: str = "cpu") -> None:
        """
        Inicializa un Frame.

        Args:
            frame: Image array en formato BGR (H, W, C)
            device: "cpu" o "gpu" para procesamiento
        """
        self.device: str = device.lower()

        if self.device == "gpu":
            try:
                self.image: Union[np.ndarray, cv.cuda_GpuMat] = cv.cuda_GpuMat()
                self.image.upload(frame)
                logger.debug("Frame cargado en GPU")
            except Exception as e:
                logger.warning(f"No se pudo usar GPU, usando CPU: {e}")
                self.image = frame
                self.device = "cpu"
        else:
            self.image = frame

    def get_image(self) -> np.ndarray:
        """
        Obtiene la imagen en formato CPU (np.ndarray).

        Si está en GPU, descarga a CPU.

        Returns:
            np.ndarray: Imagen en formato BGR
        """
        if isinstance(self.image, cv.cuda_GpuMat):
            return self.image.download()
        return self.image

    def get_dimensions(self) -> Tuple[int, int]:
        """
        Obtiene dimensiones de la imagen.

        Returns:
            Tuple[int, int]: (width, height) en píxeles
        """
        if isinstance(self.image, cv.cuda_GpuMat):
            size = self.image.size()
            return size[0], size[1]  # Width, Height
        return self.image.shape[1], self.image.shape[0]

    def resize(self, width: int, height: int) -> None:
        """
        Redimensiona la imagen.

        Args:
            width: Ancho destino en píxeles
            height: Alto destino en píxeles
        """
        try:
            if isinstance(self.image, cv.cuda_GpuMat):
                self.image = cv.cuda.resize(self.image, (width, height))
            else:
                self.image = cv.resize(self.image, (width, height))
            logger.debug(f"Frame redimensionado a {width}x{height}")
        except Exception as e:
            logger.error(f"Error al redimensionar frame: {e}")

    def crop(self, x: int, y: int, w: int, h: int) -> None:
        """
        Recorta la imagen.

        Args:
            x: Esquina X superior izquierda
            y: Esquina Y superior izquierda
            w: Ancho de la región
            h: Alto de la región
        """
        try:
            if isinstance(self.image, cv.cuda_GpuMat):
                self.image = cv.cuda_GpuMat(self.image, (x, y, w, h))
            else:
                self.image = self.image[y : y + h, x : x + w]
            logger.debug(f"Frame recortado a ({x}, {y}, {w}, {h})")
        except Exception as e:
            logger.error(f"Error al recortar frame: {e}")

    def draw_box(
        self,
        box: Tuple[int, int, int, int],
        title: Optional[str] = None,
        color: Tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2,
    ) -> None:
        """
        Dibuja un rectángulo en la imagen.

        Args:
            box: Tupla (x1, y1, x2, y2)
            title: Texto a mostrar encima del box
            color: Color BGR del rectángulo
            thickness: Grosor de línea en píxeles
        """
        try:
            img = self.get_image()
            cv.rectangle(img, (box[0], box[1]), (box[2], box[3]), color, thickness)
            if title:
                cv.putText(
                    img,
                    title,
                    (box[0], box[1] - 10),
                    cv.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    2,
                )

            if self.device == "gpu":
                self.image.upload(img)
            else:
                self.image = img
        except Exception as e:
            logger.error(f"Error al dibujar box: {e}")

    def save(self, path: str) -> bool:
        """
        Guarda la imagen a archivo.

        Args:
            path: Ruta del archivo destino

        Returns:
            bool: True si se guardó exitosamente
        """
        try:
            img = self.get_image()
            success = cv.imwrite(path, img)
            if success:
                logger.info(f"Frame guardado en: {path}")
            else:
                logger.error(f"No se pudo guardar frame en: {path}")
            return success
        except Exception as e:
            logger.error(f"Error al guardar frame: {e}")
            return False

    def release(self) -> None:
        """Libera recursos de GPU si está en uso."""
        try:
            if isinstance(self.image, cv.cuda_GpuMat):
                self.image.release()
                logger.debug("Frame GPU liberado")
        except Exception as e:
            logger.error(f"Error al liberar frame: {e}")

    def is_object_inside_box(self, obj: Any, box: Tuple[int, int, int, int]) -> bool:
        """
        Verifica si un objeto está completamente dentro de un box.

        Args:
            obj: Objeto con atributos x1, y1, x2, y2
            box: Tupla (x1, y1, x2, y2)

        Returns:
            bool: True si el objeto está dentro del box
        """
        return (
            obj.x1 >= box[0]
            and obj.y1 >= box[1]
            and obj.x2 <= box[2]
            and obj.y2 <= box[3]
        )

    def find_max_contour_by_color(self, colorRanges: list, kernelSize=(5, 5)):
        img = self.get_image()
        combinedMask = None

        for lower, upper in colorRanges:
            mask = cv.inRange(img, lower, upper)
            if combinedMask is None:
                combinedMask = mask
            else:
                combinedMask = cv.bitwise_or(combinedMask, mask)

        kernel = np.ones(kernelSize, np.uint8)
        maskClean = cv.morphologyEx(combinedMask, cv.MORPH_OPEN, kernel)
        maskClean = cv.morphologyEx(maskClean, cv.MORPH_CLOSE, kernel)

        contours, _ = cv.findContours(
            maskClean, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            return None

        return max(contours, key=cv.contourArea)
