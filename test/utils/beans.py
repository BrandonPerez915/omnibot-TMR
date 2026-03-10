import cv2 as cv
import numpy as np

"""
Este paquete contiene funciones auxiliares para el procesamiento de imagenes
relacionadas con la deteccion de granos
"""


def getBeanColor(img: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    """
    Obtiene el color promedio de una región de interés (ROI) definida por un box.
    Args:
        img (np.ndarray): La imagen de entrada en formato BGR.
        box (tuple[int, int, int, int]): Las coordenadas del box en formato (x1, y1, x2, y2).
    Returns:
        np.ndarray: El color promedio en formato HSV.
    Raises:
        ValueError: Si la región de interés está vacía.
    """
    x1, y1, x2, y2 = box
    beanROI = img[y1:y2, x1:x2]

    if beanROI.size == 0:
        raise ValueError(
            "La región de interés está vacía. Verifica las coordenadas del box."
        )

    averageRGB = cv.mean(beanROI)[:3]
    averageHSV = cv.cvtColor(np.uint8([[averageRGB]]), cv.COLOR_BGR2HSV)[0][0]

    return averageHSV


def getBeanLabel(colorHSV: np.ndarray) -> str:
    h, s, v = colorHSV

    if v < 55:
        return "Negro"

    if (h <= 10) or (h >= 160):
        return "Rojo"

    elif 11 <= h <= 25:
        return "Naranja"

    elif 26 <= h <= 35:
        return "Amarillo"

    elif 36 <= h <= 85:
        return "Verde"

    elif 86 <= h <= 130:
        return "Azul"

    return "Desconocido"
