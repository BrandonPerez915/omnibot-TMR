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

        self.box_width = self.x2 - self.x1
        self.box_height = self.y2 - self.y1
        self.center = (
            int(self.x1 + self.box_width / 2),
            int(self.y1 + self.box_height / 2),
        )

        self.state = None

    def get_roi(self, frame):
        """Obtiene la región de interés (ROI) de este grano a partir de las
        coordenadas del bounding box.

        Args:
            frame (np.ndarray): La imagen de entrada en formato BGR.
        Returns:
            np.ndarray: La región de interés del grano en formato BGR.
        """

        return frame[self.y1 : self.y2, self.x1 : self.x2]
