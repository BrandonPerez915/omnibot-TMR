import numpy as np
import cv2 as cv


class Bean:
    def __init__(self, box, confidence):
        """
        Args:
            box: Objeto box de Ultralytics o tensor con [x1, y1, x2, y2]
            confidence (float): Confianza de la detección
        """
        self.coords = box
        self.confidence = float(confidence)

        self.x1 = int(box[0])
        self.y1 = int(box[1])
        self.x2 = int(box[2])
        self.y2 = int(box[3])

        self.boxWidth = self.x2 - self.x1
        self.boxHeight = self.y2 - self.y1
        self.center = (
            int(self.x1 + self.boxWidth / 2),
            int(self.y1 + self.boxHeight / 2),
        )

        # Se utiliza Lab (Luminancia, a, b) para una mejor separación de colores bajo diferentes condiciones de iluminación
        self.l, self.a, self.b = None, None, None
        self.colorName = None

    def getROI(self, frame):
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

    def setLab(self, frame):
        """Calcula y asigna los valores Lab del grano a partir de su ROI en la imagen.

        Args:
            frame (np.ndarray): La imagen de entrada en formato BGR.
        """
        roi = self.getROI(frame)
        if roi.size == 0:
            self.l, self.a, self.b = 0, 0, 0
            return

        labROI = cv.cvtColor(roi, cv.COLOR_BGR2LAB)

        mean = cv.mean(labROI)  # Devuelve (L_mean, A_mean, B_mean)

        self.l = int(mean[0])
        self.a = int(mean[1])
        self.b = int(mean[2])
