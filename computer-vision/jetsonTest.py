from ultralytics import YOLO
import cv2 as cv

from utils.results import filterResults

# sudo /opt/nvidia/jetson-io/jetson-io.py
# gst-launch-1.0 nvarguscamerasrc ! 'video/x-raw(memory:NVMM),width=1280,height=720,framerate=30/1' ! nvvidconv ! xvimagesink

MODEL_PATH = "./model/model.engine"  # Ruta al modelo entrenado

model = YOLO(MODEL_PATH, task='detect')

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
        "video/x-raw(memory:NVMM), width=%d, height=%d, format=NV12, framerate=%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=%d, height=%d, format=BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=BGR ! appsink drop=True"       
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

pipeline = gstreamer_pipeline(sensor_id=0, flip_method=0, display_width=640, display_height=480)
cap = cv.VideoCapture(pipeline, cv.CAP_GSTREAMER)

while True:
    ret, frame = cap.read()

    if not ret:
        break

    # Dibujar box en el centro del frame
    cv.rectangle(
        frame,
        (frame.shape[1] // 2 - 100, frame.shape[0] // 2 - 100),
        (frame.shape[1] // 2 + 100, frame.shape[0] // 2 + 100),
        (255, 255, 255),
        2,
    )

    rawResults = model.predict(frame, conf=0.2, verbose=False)[0]
    data = filterResults(rawResults, frame)

    for bean in data["beans"]:
        color = None
        if bean.colorName == "Sobremaduro":
            color = (0, 0, 0)
        elif bean.colorName == "Maduro":
            color = (0, 0, 255)
        else:
            color = (0, 255, 0)

        cv.rectangle(frame, (bean.x1, bean.y1), (bean.x2, bean.y2), color, 2)
        label_text = bean.colorName
        cv.putText(
            frame,
            label_text,
            (bean.x1, bean.y1 - 10),
            cv.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2,
        )

    # for tree in data["trees"]:
    #     cv.rectangle(frame, (tree.x1, tree.y1), (tree.x2, tree.y2), (255, 0, 0), 2)

    # Verificar si hay granos dentro del box central
    central_box = {
        "x1": frame.shape[1] // 2 - 100,
        "y1": frame.shape[0] // 2 - 100,
        "x2": frame.shape[1] // 2 + 100,
        "y2": frame.shape[0] // 2 + 100,
    }
    for bean in data["beans"]:
        if (
            bean.x1 >= central_box["x1"]
            and bean.y1 >= central_box["y1"]
            and bean.x2 <= central_box["x2"]
            and bean.y2 <= central_box["y2"]
        ):
            print(f"Grano detectado dentro del box central: {bean.colorName}")

    cv.imshow("Result", frame)
    if cv.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv.destroyAllWindows()
