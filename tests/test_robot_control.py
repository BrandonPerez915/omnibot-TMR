"""Unit tests for the robot_control sub-system."""

from __future__ import annotations

from unittest.mock import MagicMock, call

import numpy as np
import pytest

from robot_control.actuators.motor_controller import MotorController
from robot_control.motion.omni_drive import OmniDrive


# ---------------------------------------------------------------------------
# MotorController
# ---------------------------------------------------------------------------


class TestMotorController:
    def _make_motor(self, motor_id=0):
        comm = MagicMock()
        return MotorController(motor_id=motor_id, comm=comm), comm

    def test_invalid_motor_id_raises(self):
        comm = MagicMock()
        with pytest.raises(ValueError):
            MotorController(motor_id=3, comm=comm)

    def test_set_speed_sends_correct_payload(self):
        motor, comm = self._make_motor(motor_id=1)
        motor.set_speed(2.5)
        comm.send.assert_called_once_with(b"M1:2.5000\n")

    def test_stop_sends_zero(self):
        motor, comm = self._make_motor(motor_id=2)
        motor.stop()
        comm.send.assert_called_once_with(b"M2:0.0000\n")

    def test_current_speed_tracks_last_command(self):
        motor, _ = self._make_motor()
        motor.set_speed(3.14)
        assert motor.current_speed == pytest.approx(3.14)

    def test_stop_sets_current_speed_to_zero(self):
        motor, _ = self._make_motor()
        motor.set_speed(5.0)
        motor.stop()
        assert motor.current_speed == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# OmniDrive
# ---------------------------------------------------------------------------


class TestOmniDrive:
    def _make_drive(self, wheel_radius=0.05, robot_radius=0.15):
        comm = MagicMock()
        drive = OmniDrive(
            wheel_radius=wheel_radius,
            robot_radius=robot_radius,
            comm=comm,
        )
        return drive, comm

    def test_stop_sends_zero_speeds(self):
        drive, comm = self._make_drive()
        drive.stop()
        sent = comm.send.call_args[0][0].decode("ascii")
        assert sent.startswith("W:")
        parts = sent[2:].split(",")
        for p in parts:
            assert float(p) == pytest.approx(0.0)

    def test_set_velocity_calls_send(self):
        drive, comm = self._make_drive()
        drive.set_velocity(0.1, 0.0, 0.0)
        comm.send.assert_called_once()

    def test_ik_matrix_shape(self):
        drive, _ = self._make_drive()
        assert drive._ik_matrix.shape == (3, 3)

    def test_speed_is_clamped(self):
        drive, comm = self._make_drive()
        # A huge forward velocity should be clamped to max_speed
        drive.set_velocity(vx=1000.0, vy=0.0, omega=0.0)
        sent = comm.send.call_args[0][0].decode("ascii")
        parts = sent[2:].split(",")
        wheel_speeds = [abs(float(p)) for p in parts]
        assert max(wheel_speeds) <= drive.max_speed + 1e-6

    def test_move_toward_calls_set_velocity(self):
        drive, comm = self._make_drive()
        target = MagicMock()
        target.centroid = (320.0, 240.0)  # image center → no movement
        drive.move_toward(target)
        sent = comm.send.call_args[0][0].decode("ascii")
        parts = sent[2:].split(",")
        # At image center, vx=0 and vy=0 so all wheel speeds should be ~0
        for p in parts:
            assert abs(float(p)) == pytest.approx(0.0, abs=1e-4)

    def test_symmetric_forward_motion(self):
        """Moving purely forward (vx > 0, vy = 0, ω = 0) should produce
        wheel speeds symmetric about the robot's forward axis."""
        drive, _ = self._make_drive()
        w1, w2, w3 = drive._inverse_kinematics(0.1, 0.0, 0.0)
        # For a symmetric 3-wheel config, wheel 0 is at 0° so it contributes
        # no forward torque; wheels 1 and 2 should be equal and opposite.
        assert abs(w2 + w3) < 1e-9  # symmetric
