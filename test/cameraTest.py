from ultralytics import YOLO
import cv2 as cv
import numpy as np

# sudo /opt/nvidia/jetson-io/jetson-io.py
# gst-launch-1.0 nvarguscamerasrc ! 'video/x-raw(memory:NVMM),width=1280,height=720,framerate=30/1' ! nvvidconv ! xvimagesink

MODEL_PATH = "../model/model.pt"  # Ruta al modelo entrenado

model = YOLO(MODEL_PATH, task='detect')
# TODO: Investigar como implementar la optimizacion de ultralytics con CUDA
# model.export(format="engine", device=0, half=True, workspace=4)

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

pipeline = gstreamer_pipeline(sensor_id=0, flip_method=0)
cap = cv.VideoCapture(pipeline, cv.CAP_GSTREAMER)

while True:
    ret, frame = cap.read()
    if not ret: break

    results = model.predict(frame, conf=0.25, verbose=False)[0].numpy()

    if results is not None:
        for box in results.boxes:
            r = box.xyxy[0].astype(int)
            labelId = int(box.cls[0])
            labelName = "Bean" if labelId == 0 else "Tree" 
            
            cv.rectangle(frame, (r[0], r[1]), (r[2], r[3]), (0, 255, 0), 2)
            cv.putText(frame, labelName, (r[0], r[1]-10), cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    cv.imshow("Optimized", frame)
    if cv.waitKey(1) & 0xFF == ord("q"): break

cap.release()
cv.destroyAllWindows()
