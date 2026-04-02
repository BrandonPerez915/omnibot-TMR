import cv2 as cv
import time

from entities.Robot import Robot
from entities.Frame import Frame

from utils.camera import openCamera

import spiCommunication as spiComm

if __name__ == "__main__":
    imxCamera = openCamera(0, 'imx-219')
    webcamCamera = openCamera(2, 'webcam')

    robot = Robot(cameras=[imxCamera, webcamCamera])
    # Start command
    spiComm.sendCommand('E')
    while robot.isPoolInFront():
        ret, frame = webcamCamera.read()
        if not ret: break
    
        robot.currentFrame = Frame(frame, device="cpu")

        cv.imshow("Webcam View", robot.currentFrame.getImage())
        if cv.waitKey(1) & 0xFF == ord('q'):
            break

        print("¡Piscina detectada frente al robot!")
    
    spiComm.sendCommand("F")
    
    commandSend = False
    while True:
        ret, frame = imxCamera.read()
        if not ret: break

        robot.currentFrame = Frame(frame, device="cpu")

        cv.imshow("Imx View", robot.currentFrame.getImage())
        if cv.waitKey(1) & 0xFF == ord('q'):
            break

        if robot.isBeanInFront() and not commandSend:
            commandSend = True
            spiComm.sendCommand('O')
            break



    imxCamera.release()
    webcamCamera.release()
    cv.destroyAllWindows()