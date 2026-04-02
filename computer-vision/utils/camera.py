import cv2 as cv

def openCamera(cameraId, cameraType):
    pipeline = getPipeline(cameraId, cameraType)

    cap = cv.VideoCapture(pipeline, cv.CAP_GSTREAMER)
    
    if not cap.isOpened():
        raise IOError(f"Cannot open camera with ID {cameraId} and type {cameraType}")
    
    return cap


def getPipeline(cameraId, cameraType):
    if cameraType.lower() == 'webcam':

        captureWidth = 640
        captureHeight = 480
        framerate = 30
        # Pipeline for Webcam USB (MJPEG)
        return (
            f"v4l2src device=/dev/video{cameraId} ! "
            f"image/jpeg, width={captureWidth}, height={captureHeight}, framerate={framerate}/1 ! "
            "jpegdec ! videoconvert ! video/x-raw, format=BGR ! "
            "appsink drop=True"
        )

    elif cameraType.lower() == 'imx-219':

        captureWidth=1280
        captureHeight=720
        framerate=30
        flipMethod=2
        displayWidth=640
        displayHeight=480
        # Pipeline for IMX219 on Jetson Orin Nano (CSI)
        return (
            f"nvarguscamerasrc sensor-id={cameraId} ! "
            f"video/x-raw(memory:NVMM), width={captureWidth}, height={captureHeight}, format=NV12, framerate={framerate}/1 ! "
            f"nvvidconv flip-method={flipMethod} ! "
            f"video/x-raw, width={displayWidth}, height={displayHeight}, format=BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=BGR ! appsink drop=True"       
        )
    