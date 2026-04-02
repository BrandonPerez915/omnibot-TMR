import cv2 as cv
import numpy as np

class Frame:
    def __init__(self, frame: np.ndarray, device="cpu"):
        self.device = device.lower()
        if self.device == "gpu":
            self.image = cv.cuda_GpuMat()
            self.image.upload(frame)
        else:
            self.image = frame
    
    def getImage(self):
        if isinstance(self.image, cv.cuda_GpuMat):
            return self.image.download()
        return self.image
    
    def getDimensions(self):
        if isinstance(self.image, cv.cuda_GpuMat):
            size = self.image.size() 
            return size[0], size[1] # Width, Height
        return self.image.shape[1], self.image.shape[0]

    def resize(self, width, height):
        if isinstance(self.image, cv.cuda_GpuMat):
            self.image = cv.cuda.resize(self.image, (width, height))
        else:
            self.image = cv.resize(self.image, (width, height))

    def crop(self, x, y, w, h):
        if isinstance(self.image, cv.cuda_GpuMat):
            # GpuMat uses Rect: (x, y, width, height)
            self.image = cv.cuda_GpuMat(self.image, (x, y, w, h))
        else:
            self.image = self.image[y:y+h, x:x+w]

    def drawBox(self, box, title=None, color=(0, 255, 0), thickness=2):
        #Draws a box. Requires CPU download if currently on GPU.S
        img = self.getImage()
        cv.rectangle(img, (box[0], box[1]), (box[2], box[3]), color, thickness)
        if title:
            cv.putText(img, title, (box[0], box[1] - 10), cv.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
        if self.device == "gpu":
            self.image.upload(img)
        else:
            self.image = img

    def save(self, path):
        img = self.getImage()
        cv.imwrite(path, img)
    
    def release(self):
        if isinstance(self.image, cv.cuda_GpuMat):
            self.image.release()

    def isObjectInsideBox(self, obj, box: tuple):
        """
        box format: (x1, y1, x2, y2)
        obj must have x1, y1, x2, y2 attributes
        """
        return (
            obj.x1 >= box[0]
            and obj.y1 >= box[1]
            and obj.x2 <= box[2]
            and obj.y2 <= box[3]
        )
    
    def findMaxContourByColor(self, colorRanges: list, kernelSize=(5, 5)):
        img = self.getImage()
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
        
        contours, _ = cv.findContours(maskClean, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
            
        return max(contours, key=cv.contourArea)
    
