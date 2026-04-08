import cv2 as cv
import numpy as np

from computer_vision.utils import open_camera, close_camera

nothing = lambda x: None

camera = open_camera(1, "webcam")

cv.namedWindow("Calibracion")
cv.resizeWindow("Calibracion", 400, 300)

cv.createTrackbar("L_min", "Calibracion", 80, 255, nothing)
cv.createTrackbar("a_min", "Calibracion", 175, 255, nothing)
cv.createTrackbar("b_min", "Calibracion", 110, 255, nothing)

cv.createTrackbar("L_max", "Calibracion", 255, 255, nothing)
cv.createTrackbar("a_max", "Calibracion", 255, 255, nothing)
cv.createTrackbar("b_max", "Calibracion", 210, 255, nothing)

print("Presiona 'q' en cualquier ventana de video para salir.")

kernel = np.ones((5, 5), np.uint8)

while True:
    ret, frame = camera.read()
    if not ret:
        print("Error al capturar la cámara")
        break

    frame_lab = cv.cvtColor(frame, cv.COLOR_BGR2LAB)

    l_min = cv.getTrackbarPos("L_min", "Calibracion")
    a_min = cv.getTrackbarPos("a_min", "Calibracion")
    b_min = cv.getTrackbarPos("b_min", "Calibracion")

    l_max = cv.getTrackbarPos("L_max", "Calibracion")
    a_max = cv.getTrackbarPos("a_max", "Calibracion")
    b_max = cv.getTrackbarPos("b_max", "Calibracion")

    lower_bound = np.array([l_min, a_min, b_min])
    upper_bound = np.array([l_max, a_max, b_max])

    mask = cv.inRange(frame_lab, lower_bound, upper_bound)

    mask_clean = cv.morphologyEx(mask, cv.MORPH_OPEN, kernel)
    mask_clean = cv.morphologyEx(mask_clean, cv.MORPH_CLOSE, kernel)

    result = cv.bitwise_and(frame, frame_lab, mask=mask_clean)

    cv.imshow("Original", frame)
    cv.imshow("Mascara (Blanco = Detectado)", mask_clean)
    cv.imshow("Resultado Color", result)

    if cv.waitKey(1) & 0xFF == ord("q"):
        break

close_camera(camera)
cv.destroyAllWindows()
