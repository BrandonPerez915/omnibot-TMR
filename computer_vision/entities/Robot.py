import time
import cv2 as cv
import numpy as np
from ultralytics import YOLO

from utils import filter_results
from entities import Frame
from constants import MODEL_DIR, SPICommands
from communication import SPIManager


class Robot:
    MIN_POOL_AREA = 5000

    model = YOLO(MODEL_DIR / "model.engine", task="detect")

    def __init__(self, cameras):
        self.name = "OmniBot"
        self.cameras = cameras
        self.SPIManager = SPIManager(port=0, device=0, max_speed_hz=1000000, mode=0)

        # El primer frame se obtiene de la webcam para detección de piscina
        ret, frame = self.cameras[1].read()
        self.current_frame = Frame(frame, device="cpu") if ret else None

    def get_frame(self, camera_id: int, device: str = "cpu") -> Frame:
        ret, frame = self.cameras[camera_id].read()
        return Frame(frame, device=device) if ret else None

    def release_cameras(self):
        for cam in self.cameras:
            cam.release()

    def is_pool_in_front(self):
        if self.current_frame is None:
            return False

        img = self.current_frame.get_image()

        # Convertir a LAB para aplicar la mascara de color
        imgLAB = cv.cvtColor(img, cv.COLOR_BGR2LAB)

        lowerBlue = np.array([0, 120, 0])
        upperBlue = np.array([255, 255, 110])

        self.current_frame.image = imgLAB
        maxContour = self.current_frame.find_max_contour_by_color(
            [(lowerBlue, upperBlue)]
        )

        # Revert back to BGR for drawing
        self.current_frame.image = img

        if maxContour is not None:
            area = cv.contourArea(maxContour)
            if area >= Robot.MIN_POOL_AREA:
                return True

    def is_bean_in_front(self):
        if self.current_frame is None:
            return False

        beans = filter_results(
            Robot.model.predict(
                self.current_frame.get_image(), conf=0.5, verbose=False
            )[0]
        )

        w, h = self.current_frame.get_dimensions()
        centralBox = (w // 2 - 100, h // 2 - 100, w // 2 + 100, h // 2 + 100)

        self.current_frame.draw_box(
            centralBox, title="Detection Box", color=(255, 255, 255)
        )

        beanInCenter = False

        for bean in beans:
            if bean.colorName == "Sobremaduro":
                color = (0, 0, 0)
            elif bean.colorName == "Maduro":
                color = (0, 0, 255)
            else:
                color = (0, 255, 0)

            self.current_frame.draw_box(
                (bean.x1, bean.y1, bean.x2, bean.y2), title=bean.colorName, color=color
            )

            if self.current_frame.is_object_inside_box(bean, centralBox):
                print(f"Grano detectado dentro del box central: {bean.colorName}")
                beanInCenter = True

        return beanInCenter

    def begin_secuense(self):
        self.SPIManager.send_command(SPICommands.START)

    def go_straight(self):
        self.SPIManager.send_command(SPICommands.STRAIGHT)

    def take_bean(self):
        self.SPIManager.send_command(SPICommands.STOP)
        # Lógica para activar el mecanismo de recolección
