"""Omni-drive kinematics and high-level movement commands.

A three-wheeled omni robot has wheels mounted at 0°, 120°, and 240°
relative to the robot's forward axis.  This module translates a desired
body-frame velocity ``(vx, vy, ω)`` into individual wheel angular
velocities using standard inverse kinematics.
"""

from __future__ import annotations

import math
from typing import Tuple

import numpy as np


class OmniDrive:
    """Omni-drive controller for a 3-wheel holonomic robot.

    Args:
        wheel_radius: Radius of each omni wheel in metres.
        robot_radius: Distance from the robot center to each wheel in metres.
        comm:         Communication object with a ``send(data: bytes)`` method.
        max_speed:    Maximum wheel angular velocity in rad/s (safety clamp).
        tracking_gain: Proportional gain used by :meth:`move_toward` to scale
                       the normalized image error into a velocity command.
                       Tune this value for your competition environment.
    """

    # Wheel mounting angles for a symmetric 3-wheel configuration
    _WHEEL_ANGLES_DEG = (0.0, 120.0, 240.0)

    def __init__(
        self,
        wheel_radius: float,
        robot_radius: float,
        comm,
        max_speed: float = 20.0,
        tracking_gain: float = 0.5,
    ) -> None:
        self.wheel_radius = wheel_radius
        self.robot_radius = robot_radius
        self.comm = comm
        self.max_speed = max_speed
        self.tracking_gain = tracking_gain

        # Pre-compute the inverse-kinematics matrix (3×3)
        self._ik_matrix = self._build_ik_matrix()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_velocity(self, vx: float, vy: float, omega: float) -> None:
        """Command a body-frame velocity.

        Args:
            vx:    Forward velocity in m/s (robot's X axis).
            vy:    Lateral velocity in m/s (robot's Y axis).
            omega: Rotational velocity in rad/s (positive = counter-clockwise).
        """
        wheel_speeds = self._inverse_kinematics(vx, vy, omega)
        self._send_wheel_speeds(wheel_speeds)

    def move_toward(self, target) -> None:
        """Move the robot toward a tracked target.

        Args:
            target: A :class:`TrackedObject` (or any object with a
                    ``centroid`` attribute ``(cx, cy)``).

        Note:
            This is a placeholder proportional controller.  Replace with a
            proper PID or trajectory planner for competition use.
        """
        cx, cy = target.centroid
        # Normalized error: assume image center is (320, 240) for 640×480
        ex = (cx - 320.0) / 320.0
        ey = (cy - 240.0) / 240.0

        self.set_velocity(vx=-ey * self.tracking_gain, vy=ex * self.tracking_gain, omega=0.0)

    def stop(self) -> None:
        """Immediately stop all wheels."""
        self._send_wheel_speeds((0.0, 0.0, 0.0))

    # ------------------------------------------------------------------
    # Kinematics
    # ------------------------------------------------------------------

    def _build_ik_matrix(self) -> np.ndarray:
        """Build the 3×3 inverse-kinematics matrix."""
        rows = []
        for deg in self._WHEEL_ANGLES_DEG:
            rad = math.radians(deg)
            # Each row: [-sin(θ), cos(θ), R]
            rows.append([-math.sin(rad), math.cos(rad), self.robot_radius])
        return np.array(rows, dtype=float)

    def _inverse_kinematics(
        self, vx: float, vy: float, omega: float
    ) -> Tuple[float, float, float]:
        """Convert body velocity to wheel angular velocities.

        Returns:
            Tuple of three wheel angular velocities in rad/s.
        """
        body_vel = np.array([vx, vy, omega], dtype=float)
        wheel_linear = self._ik_matrix @ body_vel
        wheel_angular = wheel_linear / self.wheel_radius

        # Safety clamp
        max_abs = max(abs(w) for w in wheel_angular)
        if max_abs > self.max_speed:
            wheel_angular = wheel_angular * (self.max_speed / max_abs)

        return tuple(wheel_angular.tolist())

    # ------------------------------------------------------------------
    # Communication
    # ------------------------------------------------------------------

    def _send_wheel_speeds(self, speeds: Tuple[float, float, float]) -> None:
        """Encode wheel speeds and transmit over the communication layer."""
        # Simple CSV encoding: "W:<w0>,<w1>,<w2>\n"
        payload = f"W:{speeds[0]:.4f},{speeds[1]:.4f},{speeds[2]:.4f}\n"
        self.comm.send(payload.encode("ascii"))
