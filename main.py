"""
omnibot-TMR main entry point.

Starts the full robot pipeline:
  1. Initialises configuration.
  2. Launches the computer-vision detection/tracking loop.
  3. Passes detections to the robot-control layer.
  4. Manages communication with the hardware.
"""

import yaml

from computer_vision.detection.object_detector import ObjectDetector
from computer_vision.tracking.tracker import Tracker
from robot_control.motion.omni_drive import OmniDrive
from robot_control.sensors.sensor_interface import SensorInterface
from communication.serial_comm import SerialComm


def load_config(path: str = "config/robot_config.yaml") -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def main() -> None:
    cfg = load_config()

    # --- Communication ---
    comm = SerialComm(
        port=cfg["communication"]["port"],
        baud_rate=cfg["communication"]["baud_rate"],
    )

    # --- Sensors ---
    sensor = SensorInterface(comm=comm)

    # --- Robot control ---
    drive = OmniDrive(
        wheel_radius=cfg["robot"]["wheel_radius"],
        robot_radius=cfg["robot"]["robot_radius"],
        comm=comm,
        tracking_gain=cfg["robot"].get("tracking_gain", 0.5),
    )

    # --- Computer vision ---
    detector = ObjectDetector(model_path=cfg["computer_vision"]["model_path"])
    tracker = Tracker()

    print("[omnibot-TMR] Pipeline initialised. Starting main loop …")
    try:
        while True:
            # 1. Read sensor data
            sensor_data = sensor.read()

            # 2. Detect & track objects
            frame = sensor_data.get("frame")
            if frame is not None:
                detections = detector.detect(frame)
                tracked_objects = tracker.update(detections)
            else:
                tracked_objects = []

            # 3. Decide and move (placeholder strategy)
            if tracked_objects:
                # Simple demo: move toward the first tracked object
                target = tracked_objects[0]
                drive.move_toward(target)
            else:
                drive.stop()

    except KeyboardInterrupt:
        print("\n[omnibot-TMR] Shutting down …")
    finally:
        drive.stop()
        comm.close()


if __name__ == "__main__":
    main()
