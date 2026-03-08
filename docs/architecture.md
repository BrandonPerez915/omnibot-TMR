# omnibot-TMR Architecture

## System Overview

```
┌─────────────────────────────────────────────────────┐
│                  Main Compute Unit                  │
│              (Raspberry Pi / Laptop)                │
│                                                     │
│  ┌──────────────────┐   ┌───────────────────────┐  │
│  │  computer_vision │   │    robot_control       │  │
│  │  ───────────────  │   │  ───────────────────  │  │
│  │  detection/      │──▶│  motion/omni_drive     │  │
│  │  tracking/       │   │  sensors/              │  │
│  │  utils/          │   │  actuators/            │  │
│  └──────────────────┘   └───────────┬───────────┘  │
│                                     │               │
│                    ┌────────────────▼─────────────┐ │
│                    │       communication/          │ │
│                    │       serial_comm             │ │
│                    └────────────────┬─────────────┘ │
└─────────────────────────────────────┼───────────────┘
                                      │ USB / UART
┌─────────────────────────────────────▼───────────────┐
│            Microcontroller  (Arduino / STM32)        │
│          Motor drivers  ·  Encoders  ·  IMU          │
└──────────────────────────────────────────────────────┘
```

## Component Descriptions

### `computer_vision/`
- **detection/** – YOLO-based object detector. Produces `Detection` objects
  with bounding-box, confidence, class ID and label.
- **tracking/** – Centroid-based multi-object tracker. Associates detections
  across frames and returns `TrackedObject` instances with persistent IDs.
- **utils/** – Image resize, colour-space conversion, annotation helpers.

### `robot_control/`
- **motion/omni_drive.py** – Inverse kinematics for a symmetric 3-wheel
  holonomic drive. Converts body-frame `(vx, vy, ω)` into per-wheel speeds.
- **sensors/sensor_interface.py** – Reads encoder counts and IMU data from
  the microcontroller.
- **actuators/motor_controller.py** – Sends individual motor commands.

### `communication/`
- **serial_comm.py** – ASCII line-protocol serial wrapper with context-manager
  support.

### `config/`
- **robot_config.yaml** – All tunable parameters (wheel geometry, serial port,
  model path, camera settings).

## Data Flow

```
Camera frame
    │
    ▼
ObjectDetector.detect(frame)  →  List[Detection]
    │
    ▼
Tracker.update(detections)    →  List[TrackedObject]
    │
    ▼
OmniDrive.move_toward(target) →  (vx, vy, ω)
    │
    ▼
SerialComm.send(wheel_speeds) →  MCU → motors
```

## Branch Strategy

| Branch | Responsible Module |
|--------|--------------------|
| `computer-vision` | `computer_vision/` |
| `robot-control`   | `robot_control/`   |
| `communication`   | `communication/`   |
| `integration`     | Full pipeline      |
| `main`            | Stable releases    |
