# communication/

Communication sub-system for the omnibot-TMR.

Handles serial communication between the main compute unit (e.g. Raspberry Pi)
and the low-level microcontroller (e.g. Arduino / STM32).

## Protocol

All messages use a simple ASCII line protocol:

| Direction | Prefix | Example |
|-----------|--------|---------|
| Host → MCU | `W:` | `W:1.2300,-0.5600,0.0000\n` (wheel speeds) |
| Host → MCU | `M<id>:` | `M0:3.1400\n` (individual motor) |
| MCU → Host | `E:` | `E:1024,1024,1024\n` (encoder counts) |
| MCU → Host | `I:` | `I:45.0,0.5\n` (IMU heading, gyro_z) |

## Usage

```python
from communication.serial_comm import SerialComm

comm = SerialComm(port="/dev/ttyUSB0", baud_rate=115200)
comm.open()
comm.send(b"W:0.0000,0.0000,0.0000\n")
line = comm.read_line()
comm.close()
```
