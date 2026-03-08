"""Serial communication wrapper for the omnibot-TMR hardware interface."""

from __future__ import annotations

import time
from typing import Optional


class SerialComm:
    """Manages a serial connection to the robot's microcontroller.

    Args:
        port:      Serial port path, e.g. ``"/dev/ttyUSB0"`` or ``"COM3"``.
        baud_rate: Baud rate (default 115200).
        timeout:   Read timeout in seconds (default 0.1).
    """

    def __init__(
        self,
        port: str,
        baud_rate: int = 115200,
        timeout: float = 0.1,
    ) -> None:
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self._serial = None
        self._open()

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def _open(self) -> None:
        """Open the serial port."""
        try:
            import serial  # type: ignore

            self._serial = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=self.timeout,
            )
            time.sleep(0.1)  # Allow the MCU to reset after DTR toggle
        except ImportError as exc:
            raise RuntimeError(
                "pyserial is required for SerialComm. "
                "Install it with: pip install pyserial"
            ) from exc
        except Exception as exc:
            raise RuntimeError(
                f"Failed to open serial port '{self.port}': {exc}"
            ) from exc

    def close(self) -> None:
        """Close the serial port if it is open."""
        if self._serial and self._serial.is_open:
            self._serial.close()

    # ------------------------------------------------------------------
    # I/O
    # ------------------------------------------------------------------

    def send(self, data: bytes) -> None:
        """Write raw bytes to the serial port.

        Args:
            data: Bytes to transmit.
        """
        if self._serial is None or not self._serial.is_open:
            return
        self._serial.write(data)

    def read_line(self) -> Optional[str]:
        """Read one newline-terminated ASCII line from the serial port.

        Returns:
            Decoded string without the trailing newline, or ``None`` on timeout.
        """
        if self._serial is None or not self._serial.is_open:
            return None
        try:
            raw = self._serial.readline()
            if raw:
                return raw.decode("ascii", errors="replace").strip()
        except Exception:
            pass
        return None

    def read_bytes(self, n: int) -> bytes:
        """Read exactly *n* bytes from the serial port.

        Args:
            n: Number of bytes to read.

        Returns:
            Byte string of length up to *n*.
        """
        if self._serial is None or not self._serial.is_open:
            return b""
        return self._serial.read(n)

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self) -> "SerialComm":
        return self

    def __exit__(self, *_) -> None:
        self.close()
