import cv2 as cv
import time

from computer_vision.entities import Frame, Robot
from computer_vision.utils import open_camera, close_camera
from constants import BeanStates


def init_robot() -> Robot:
    imx_219 = open_camera(0, "imx-219")
    webcam = open_camera(1, "webcam")

    robot = Robot(cameras=[imx_219, webcam])
    return robot


def main() -> None:
    robot = init_robot()

    robot.begin_secuense()

    while robot.is_pool_in_front():
        robot.current_frame = robot.get_frame(1, device="cpu")

    robot.go_straight()

    while True:
        robot.current_frame = robot.get_frame(0, device="cpu")

        if robot.is_bean_in_front():
            robot.take_bean()

    robot.release_cameras()


if __name__ == "__main__":
    main()
