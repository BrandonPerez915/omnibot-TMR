import cv2 as cv
import numpy as np
from ultralytics import YOLO

from utils.results import filterResults

from entities.Frame import Frame

class Robot:
    MIN_POOL_AREA = 5000
    MODEL_PATH = "./model/model.engine"  

    model = YOLO(MODEL_PATH, task='detect')

    def __init__(self, cameras):
        self.name = 'OmniBot'
        self.cameras = cameras
        # The first frame is captured from the second camera (webcam) to check for the pool
        ret, frame = self.cameras[1].read()
        self.currentFrame = Frame(frame, device="cpu") if ret else None

    def isPoolInFront(self):
        if self.currentFrame is None:
            return False
        
        img = self.currentFrame.getImage()
        
        # Convert to LAB for the color mask
        imgLAB = cv.cvtColor(img, cv.COLOR_BGR2LAB)
        
        lowerBlue = np.array([0, 120, 0]) 
        upperBlue = np.array([255, 255, 110])
        
        self.currentFrame.image = imgLAB
        maxContour = self.currentFrame.findMaxContourByColor([(lowerBlue, upperBlue)])
        
        # Revert back to BGR for drawing
        self.currentFrame.image = img 

        if maxContour is not None:
            area = cv.contourArea(maxContour)
            if area >= Robot.MIN_POOL_AREA:
                return True
    
    def isBeanInFront(self):
        if self.currentFrame is None:
            return False

        beans = filterResults(Robot.model.predict(self.currentFrame.getImage(), conf=0.5, verbose=False)[0])
        
        w, h = self.currentFrame.getDimensions()
        centralBox = (w // 2 - 100, h // 2 - 100, w // 2 + 100, h // 2 + 100)

        self.currentFrame.drawBox(centralBox, title='Detection Box', color=(255, 255, 255))

        beanInCenter = False

        for bean in beans:
            if bean.colorName == "Sobremaduro":
                color = (0, 0, 0)
            elif bean.colorName == "Maduro":
                color = (0, 0, 255)
            else:
                color = (0, 255, 0)

            self.currentFrame.drawBox((bean.x1, bean.y1, bean.x2, bean.y2), title=bean.colorName, color=color)

            if self.currentFrame.isObjectInsideBox(bean, centralBox):
                print(f"Grano detectado dentro del box central: {bean.colorName}")
                beanInCenter = True

        return beanInCenter
