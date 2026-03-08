# robot_control/

Robot control sub-system for the omnibot-TMR.

## Sub-packages

| Package | Description |
|---------|-------------|
| `motion/` | Omni-drive kinematics and high-level movement commands |
| `sensors/` | Sensor interface (encoders, IMU, camera frame delivery) |
| `actuators/` | Low-level motor controller wrappers |

## Omni-Drive Overview

The omnibot uses **three omni wheels** spaced 120° apart.  
Inverse kinematics maps a desired `(vx, vy, ω)` velocity to individual
wheel speeds, which are then sent to the motor controllers via the
communication layer.

## Usage

```python
from robot_control.motion.omni_drive import OmniDrive
from communication.serial_comm import SerialComm

comm  = SerialComm(port="/dev/ttyUSB0", baud_rate=115200)
drive = OmniDrive(wheel_radius=0.05, robot_radius=0.15, comm=comm)

drive.set_velocity(vx=0.2, vy=0.0, omega=0.0)  # move forward at 0.2 m/s
drive.stop()
```
