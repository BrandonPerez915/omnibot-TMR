# omnibot-TMR

This repo contains all the computer vision and control code used in the **Omnibot** for the **Torneo Mexicano de Robotica (TMR) 2026**.

## Repository Structure

```
omnibot-TMR/
├── computer_vision/        # Computer vision pipeline (object detection, tracking, utils)
├── robot_control/          # Robot control (omni-drive kinematics, motors, sensors)
├── communication/          # Serial / network communication layer
├── config/                 # Robot configuration files
├── docs/                   # Architecture & design documentation
└── tests/                  # Unit and integration tests
```

## Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Stable, tested releases |
| `computer-vision` | Computer vision features & experiments |
| `robot-control` | Robot control algorithms & drivers |
| `communication` | Communication protocols & interfaces |
| `integration` | Integration testing of all sub-systems |

## Getting Started

### Prerequisites

- Python 3.9+
- pip

### Installation

```bash
pip install -r requirements.txt
```

### Running

```bash
# Start the full robot pipeline
python main.py
```

## Modules

### `computer_vision/`
Object detection, object tracking, and image utility helpers.
See [`computer_vision/README.md`](computer_vision/README.md).

### `robot_control/`
Omni-drive kinematics, motor control, and sensor interfaces.
See [`robot_control/README.md`](robot_control/README.md).

### `communication/`
Serial and network communication between the robot's subsystems.
See [`communication/README.md`](communication/README.md).

## Contributing

1. Fork the repository.
2. Create a feature branch from the appropriate sub-system branch.
3. Open a Pull Request targeting that sub-system branch.

