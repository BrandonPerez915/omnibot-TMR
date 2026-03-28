import cv2 as cv
from utils.results import filterResults

MODEL_PATH = "./model/model.pt"
SAVE_PATH = "../dataset"

clickDetected = False
currentImg = 1

def mouse_click(event, x, y, flags, param):
    global clickDetected, currentImg
    if event == cv.EVENT_LBUTTONDOWN:
        clickDetected = True
        currentImg += 1

def gstreamer_pipeline(sensor_id=0, capture_width=1280, capture_height=720, framerate=30, flip_method=0, display_width=640, display_height=480):
    return (
        "nvarguscamerasrc sensor-id=%d ! "
        "video/x-raw(memory:NVMM), width=%d, height=%d, format=NV12, framerate=%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=%d, height=%d, format=BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=BGR ! appsink drop=True"       
        % (sensor_id, capture_width, capture_height, framerate, flip_method, display_width, display_height)
    )

pipeline = gstreamer_pipeline(sensor_id=0, flip_method=0)
cap = cv.VideoCapture(pipeline, cv.CAP_GSTREAMER)

cv.namedWindow("Capture IMG")
cv.setMouseCallback("Capture IMG", mouse_click)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    if clickDetected:
        filename = f"{SAVE_PATH}/img{currentImg}.jpg"

        cv.imwrite(filename, frame)
        print(f" Frame guardado: {filename}")
        
        clickDetected = False

    cv.imshow("Capture IMG", frame)
    
    if cv.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv.destroyAllWindows()