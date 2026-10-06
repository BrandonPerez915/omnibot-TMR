import cv2 as cv

from constants import SAVE_PATH
from computer_vision.utils import open_camera, close_camera

click_detected = False
current_img = 1


def mouse_click(event, x, y, flags, param):
    global click_detected, current_img
    if event == cv.EVENT_LBUTTONDOWN:
        click_detected = True
        current_img += 1


camera = open_camera(0, "imx-219")
cv.namedWindow("Capture IMG")
cv.setMouseCallback("Capture IMG", mouse_click)

while True:
    ret, frame = camera.read()
    if not ret:
        break

    if click_detected:
        filename = f"{SAVE_PATH}/image{current_img}.jpg"

        cv.imwrite(filename, frame)
        print(f" Frame guardado: {filename}")

        click_detected = False

    cv.imshow("Capture IMG", frame)

    if cv.waitKey(1) & 0xFF == ord("q"):
        break

close_camera(camera)
cv.destroyAllWindows()
