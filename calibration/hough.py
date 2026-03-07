import cv2 as cv
import numpy as np

# Callback para los sliders
def nothing(x):
    pass

srcImg = cv.imread('img1.png')
if srcImg is None:
    print("Error: No se pudo cargar 'img1.png'")
    exit()


cv.namedWindow('Calibracion', cv.WINDOW_NORMAL)
cv.resizeWindow('Calibracion', 600, 600)
cv.createTrackbar('minDist', 'Calibracion', 100, 500, nothing)
cv.createTrackbar('param1', 'Calibracion', 40, 300, nothing)
cv.createTrackbar('param2', 'Calibracion', 80, 200, nothing)
cv.createTrackbar('minRadius', 'Calibracion', 10, 500, nothing)
cv.createTrackbar('maxRadius', 'Calibracion', 100, 1000, nothing)
cv.createTrackbar('blur', 'Calibracion', 2, 10, nothing)

while True:
    imgCopy = srcImg.copy()
    
    # Leer valores de sliders
    minDist = cv.getTrackbarPos('minDist', 'Calibracion')
    param1 = cv.getTrackbarPos('param1', 'Calibracion')
    param2 = cv.getTrackbarPos('param2', 'Calibracion')
    minRadius = cv.getTrackbarPos('minRadius', 'Calibracion')
    maxRadius = cv.getTrackbarPos('maxRadius', 'Calibracion')
    blur = cv.getTrackbarPos('blur', 'Calibracion')

    if minDist < 1: minDist = 1
    if param1 < 1: param1 = 1
    if param2 < 1: param2 = 1
    
    gray = cv.cvtColor(imgCopy, cv.COLOR_BGR2GRAY)
    kernelSize = (blur * 2) + 1
    gray = cv.medianBlur(gray, kernelSize)

    circles = cv.HoughCircles(
        gray, 
        cv.HOUGH_GRADIENT, 
        dp=1.2, 
        minDist=minDist,
        param1=param1, 
        param2=param2, 
        minRadius=minRadius, 
        maxRadius=maxRadius
    )

    if circles is not None:
        circles = np.uint16(np.around(circles))
        for i in circles[0, :]:
            cv.circle(imgCopy, (i[0], i[1]), i[2], (0, 255, 0), 2)
            cv.circle(imgCopy, (i[0], i[1]), 2, (0, 0, 255), 3)
    
    cv.imshow('Calibracion', imgCopy)

    if cv.waitKey(1) & 0xFF == ord('q'):
        print(f"\nValores finales seleccionados:")  
        print(f"minDist={minDist}, param1={param1}, param2={param2}, minRadius={minRadius}, maxRadius={maxRadius}")
        break

cv.destroyAllWindows()