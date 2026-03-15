import numpy as np
import cv2 as cv


class Bean:
    def __init__(self, box: tuple, confidence: float):
        """
        Args:
            box: Objeto box de Ultralytics o tensor con [x1, y1, x2, y2]
            confidence (float): Confianza de la detección
        """
        self.coords = box.xyxy[0].cpu().numpy().astype(int)
        self.confidence = float(confidence)

        self.x1, self.y1, self.x2, self.y2 = self.coords
        self.width = self.x2 - self.x1
        self.height = self.y2 - self.y1
        self.center = (int(self.x1 + self.width / 2), int(self.y1 + self.height / 2))

        self.h, self.s, self.v = None, None, None  # Valores HSV del grano
        self.colorName = None

    def getROI(self, frame: np.ndarray) -> np.ndarray:
        """Obtiene la región de interés (ROI) de este grano a partir de las
        coordenadas del bounding box.

        Args:
            frame (np.ndarray): La imagen de entrada en formato BGR.
        Returns:
            np.ndarray: La región de interés del grano en formato BGR.
        """

        return frame[self.y1 : self.y2, self.x1 : self.x2]

    def inTree(self, tree) -> bool:
        """
        Verifica si este grano está dentro de un árbol dado.
        Args:
            tree (Tree): El objeto Tree con el que se va a comparar.
        Returns:
            bool: True si el grano está dentro del árbol, False en caso contrario.
        """

        return (
            self.x1 >= tree.x1
            and self.y1 >= tree.y1
            and self.x2 <= tree.x2
            and self.y2 <= tree.y2
        )

    def __repr__(self):
        return f"Bean(Center={self.center}, Conf={self.confidence:.2f})"

    def setHSV(self, frame):
        """Calcula y asigna los valores HSV del grano a partir de su ROI en la imagen.

        Args:
            frame (np.ndarray): La imagen de entrada en formato BGR.
        """
        roi = self.getROI(frame)
        if roi.size == 0:
            self.h, self.s, self.v = 0, 0, 0
            return

        HSV_ROI = cv.cvtColor(roi, cv.COLOR_BGR2HSV)

        mean = cv.mean(HSV_ROI)  # Devuelve (H_mean, S_mean, V_mean, A_mean)

        self.h = int(mean[0])
        self.s = int(mean[1])
        self.v = int(mean[2])
