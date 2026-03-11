import cv2 as cv
import time

# Callback para el click
def clickCallback(event, x, y, flags, param):
    if event == cv.EVENT_LBUTTONDOWN:
        clickFrame = param['frame']

        imgName = f"captura_{int(time.time())}.png"
        
        cv.imwrite(imgName, clickFrame)
        print(f"Foto guardada como: {imgName}")

def gstreamer_pipeline(
    sensor_id=0,
    capture_width=1280,
    capture_height=720,
    framerate=30,
    flip_method=0,
    display_width=1280,
    display_height=720,
):
    return (
        "nvarguscamerasrc sensor-id=%d ! "
        "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, format=(string)NV12, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink drop=True"
        % (
            sensor_id,
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )

pipeline = gstreamer_pipeline(sensor_id=0, flip_method=0)
cap = cv.VideoCapture(pipeline, cv.CAP_GSTREAMER)

cv.namedWindow("Camara - Click para capturar")
datos = {'frame': None}
cv.setMouseCallback("Camara - Click para capturar", clickCallback, datos)

print("Instrucciones: Haz clic IZQUIERDO sobre la imagen para guardar un frame. Presiona 'q' para salir.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    datos['frame'] = frame

    cv.imshow("Camara - Click para capturar", frame)

    if cv.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv.destroyAllWindows()