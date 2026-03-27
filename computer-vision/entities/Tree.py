import numpy as np


class Tree:
    def __init__(self, box, confidence):
        """
        Representa un árbol detectado y contiene los granos filtrados dentro de él.
        """
        self.coords = box
        self.confidence = float(confidence)

        # Atributos calculados en base a las coordenadas del bounding box
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

        # Granos que pertenecen a este árbol
        self.beans = []

    def addBean(self, bean_obj):
        """Agrega un objeto de la clase Bean a la colección de este árbol"""
        self.beans.append(bean_obj)

    def countBeans(self):
        """Devuelve la cantidad de granos detectados en este árbol"""
        return len(self.beans)

    def __repr__(self):
        return f"Tree(Center={self.center}, BeansCount={self.countBeans()}, Conf={self.confidence:.2f})"
