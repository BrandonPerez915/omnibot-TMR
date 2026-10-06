import cv2 as cv
import time

from computer_vision.entities import Robot
from computer_vision.utils import open_camera
from constants import BeanStates
from logger import get_logger

logger = get_logger(__name__)

def init_robot() -> Robot:
    try:
        imx_219 = open_camera(0, "imx-219")
        webcam = open_camera(1, "webcam")
    except Exception as e:
        logger.error(f"Error al inicializar alguna cámara: {e}")
        return None
    logger.info("Cámaras inicializadas correctamente.")

    robot = Robot(cameras=[imx_219, webcam])
    logger.info("Robot inicializado correctamente.")
    return robot


def main() -> None:
    logger.info("Iniciando OmniBot...")

    robot = init_robot()
    if robot is None:
        logger.error("No se pudo inicializar el robot. Terminando ejecución.")
        return
    
    robot.begin_secuense()

    while robot.is_pool_in_front():
        robot.current_frame = robot.get_frame(1, device="cpu")

        cv.imshow("Webcam", robot.current_frame.get_image())
        if cv.waitKey(1) & 0xFF == ord("q"):
            break

    robot.go_straight()

    while True:
        robot.current_frame = robot.get_frame(0, device="cpu")

        if robot.is_bean_in_front():
            robot.take_bean()

        cv.imshow("IMX-219", robot.current_frame.get_image())
        if cv.waitKey(1) & 0xFF == ord("q"):
            break

    robot.release_cameras()
    robot.SPIManager.close()
    cv.destroyAllWindows()
    logger.info("OmniBot finalizado. Recursos liberados. \n")

if __name__ == "__main__":
    main()
