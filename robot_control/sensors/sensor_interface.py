"""Sensor interface – reads raw sensor data from the hardware."""

from __future__ import annotations

from typing import Any, Dict, Optional


class SensorInterface:
    """Reads sensor data from the robot via the communication layer.

    Currently supports:
    - Encoder counts (wheel odometry)
    - IMU data (heading / angular velocity)
    - Camera frame (if delivered over serial as JPEG bytes)

    Args:
        comm: Communication object with ``read_line() -> str`` and
              ``read_bytes(n) -> bytes`` methods.
    """

    def __init__(self, comm) -> None:
        self.comm = comm

    def read(self) -> Dict[str, Any]:
        """Read a snapshot of all available sensor data.

        Returns:
            Dictionary with keys:
            - ``"encoders"``  : list of three encoder tick counts.
            - ``"imu"``       : dict with ``"heading"`` (°) and ``"gyro_z"`` (°/s).
            - ``"frame"``     : NumPy BGR frame, or ``None`` if unavailable.
        """
        data: Dict[str, Any] = {
            "encoders": self._read_encoders(),
            "imu": self._read_imu(),
            "frame": self._read_camera_frame(),
        }
        return data

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _read_encoders(self):
        """Read encoder counts for all three wheels."""
        try:
            line = self.comm.read_line()
            if line and line.startswith("E:"):
                counts = [int(v) for v in line[2:].split(",")]
                return counts
        except Exception:
            pass
        return [0, 0, 0]

    def _read_imu(self) -> Dict[str, float]:
        """Read IMU heading and Z-axis angular velocity."""
        try:
            line = self.comm.read_line()
            if line and line.startswith("I:"):
                parts = line[2:].split(",")
                return {"heading": float(parts[0]), "gyro_z": float(parts[1])}
        except Exception:
            pass
        return {"heading": 0.0, "gyro_z": 0.0}

    def _read_camera_frame(self) -> Optional[Any]:
        """Read a camera frame if one is available.

        Returns ``None`` if no frame is present or on error.
        In a real system this would be replaced by a dedicated
        camera capture thread (e.g. using ``cv2.VideoCapture``).
        """
        return None
