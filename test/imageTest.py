import cv2 as cv
import numpy as np

img = cv.imread('img1.png')
if img is None:
    print("No se pudo cargar la imagen")
    exit()

grayImg = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
grayImg = cv.medianBlur(grayImg, 5)
hsvImg = cv.cvtColor(img, cv.COLOR_BGR2HSV)

# TODO: Esto requiere calibración con el color del arbol
treeColorUpper = np.array([10, 50, 50]) 
treeColorLower = np.array([20, 255, 255])
mask = cv.inRange(hsvImg, treeColorUpper, treeColorLower)

contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

x, y, w, h = 0, 0, 0, 0
if contours:
    maxContour = max(contours, key=cv.contourArea)
    x, y, w, h = cv.boundingRect(maxContour)

    
    # Region of Interest (ROI) para el árbol
    ROIGray = grayImg[y:y+h, x:x+w]
    img = cv.rectangle(
        img, 
        (x, y), 
        (x+w, y+h), 
        (255, 0, 0), 2
    )
    img = cv.putText(
        img,
        'arbol',
        (x + 10, y + 30),
        cv.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 0, 0),
        2
    )
else:
    # En caso de no encontrar contornos, la ROI es toda la imagen
    ROIGray = grayImg

circles = cv.HoughCircles(
    ROIGray, 
    cv.HOUGH_GRADIENT, 
    1, 
    minDist=50,
    param1=85, 
    param2=20, 
    minRadius=10, 
    maxRadius=20
)
if circles is not None:
    circles = np.uint16(np.around(circles))

    for i in circles[0, :]:
        center = (i[0] + x, i[1] + y)  # Ajustar coordenadas al ROI
        radius = i[2]
        cv.circle(img, center, radius, (0, 255, 0), 2)
        cv.circle(img, center, 2, (0, 0, 255), 3)
    else:
        print("No se detectaron círculos")

cv.imshow('Circulos Detectados', img)
cv.waitKey(0)
cv.destroyAllWindows()