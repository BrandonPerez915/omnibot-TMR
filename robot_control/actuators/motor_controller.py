"""Low-level motor controller wrapper."""

from __future__ import annotations


class MotorController:
    """Sends individual motor commands over the communication layer.

    Args:
        motor_id: Integer identifier for the motor (0, 1, or 2).
        comm:     Communication object with a ``send(data: bytes)`` method.
    """

    def __init__(self, motor_id: int, comm) -> None:
        if motor_id not in (0, 1, 2):
            raise ValueError(f"motor_id must be 0, 1, or 2 (got {motor_id})")
        self.motor_id = motor_id
        self.comm = comm
        self._current_speed: float = 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_speed(self, speed: float) -> None:
        """Set motor angular velocity.

        Args:
            speed: Desired angular velocity in rad/s.
                   Positive = forward, negative = reverse.
        """
        self._current_speed = speed
        payload = f"M{self.motor_id}:{speed:.4f}\n"
        self.comm.send(payload.encode("ascii"))

    def stop(self) -> None:
        """Immediately stop this motor."""
        self.set_speed(0.0)

    @property
    def current_speed(self) -> float:
        """Last commanded speed in rad/s."""
        return self._current_speed
