import cv2 as cv

from constants import ImageSizes, CameraConfig


def getPipeline(cameraId, cameraType):
    if cameraType.lower() == "webcam":

        captureWidth = ImageSizes.WEBCAM_WIDTH
        captureHeight = ImageSizes.WEBCAM_HEIGHT
        framerate = CameraConfig.FRAME_RATE
        # Pipeline for Webcam USB (MJPEG)
        return (
            f"v4l2src device=/dev/video{cameraId} ! "
            f"image/jpeg, width={captureWidth}, height={captureHeight}, framerate={framerate}/1 ! "
            "jpegdec ! videoconvert ! video/x-raw, format=BGR ! "
            "appsink drop=True"
        )

    elif cameraType.lower() == "imx-219":

        captureWidth = ImageSizes.IMX219_WIDTH
        captureHeight = ImageSizes.IMX219_HEIGHT
        framerate = CameraConfig.FRAME_RATE
        flipMethod = CameraConfig.FLIP_180
        displayWidth = ImageSizes.DISPLAY_WIDTH
        displayHeight = ImageSizes.DISPLAY_HEIGHT
        # Pipeline for IMX219 on Jetson Orin Nano (CSI)
        return (
            f"nvarguscamerasrc sensor-id={cameraId} ! "
            f"video/x-raw(memory:NVMM), width={captureWidth}, height={captureHeight}, format=NV12, framerate={framerate}/1 ! "
            f"nvvidconv flip-method={flipMethod} ! "
            f"video/x-raw, width={displayWidth}, height={displayHeight}, format=BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=BGR ! appsink drop=True"
        )


def openCamera(camera_id, camera_type):
    pipeline = getPipeline(camera_id, camera_type)

    cap = cv.VideoCapture(pipeline, cv.CAP_GSTREAMER)

    if not cap.isOpened():
        raise IOError(f"Cannot open camera with ID {camera_id} and type {camera_type}")

    return cap


def closeCamera(camera):
    camera.release()
