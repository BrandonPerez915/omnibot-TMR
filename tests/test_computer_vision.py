"""Unit tests for the computer_vision sub-system."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from computer_vision.detection.object_detector import Detection, ObjectDetector
from computer_vision.tracking.tracker import Tracker, TrackedObject
from computer_vision.utils.image_utils import bgr_to_rgb, normalize, resize_frame


# ---------------------------------------------------------------------------
# ObjectDetector
# ---------------------------------------------------------------------------


class TestObjectDetector:
    def test_init_stores_parameters(self):
        det = ObjectDetector(model_path="model.pt", confidence_threshold=0.6, device="cpu")
        assert det.confidence_threshold == 0.6
        assert det.device == "cpu"
        assert det._model is None  # lazy loading

    def test_detect_loads_model_on_first_call(self):
        det = ObjectDetector(model_path="model.pt")
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        mock_box = MagicMock()
        mock_box.xyxy = [np.array([10.0, 20.0, 100.0, 200.0])]
        mock_box.conf = [np.float32(0.9)]
        mock_box.cls = [np.int64(0)]

        mock_result = MagicMock()
        mock_result.boxes = [mock_box]
        mock_result.names = {0: "ball"}

        mock_model = MagicMock(return_value=[mock_result])

        with patch("computer_vision.detection.object_detector.YOLO", mock_model, create=True):
            # Inject fake ultralytics into sys.modules so the import works
            import sys
            fake_ultralytics = MagicMock()
            fake_ultralytics.YOLO = mock_model
            sys.modules.setdefault("ultralytics", fake_ultralytics)
            det._model = mock_model

            detections = det.detect(frame)

        assert len(detections) == 1
        assert detections[0].label == "ball"
        assert detections[0].confidence == pytest.approx(0.9, abs=0.01)


class TestDetection:
    def test_detection_fields(self):
        d = Detection(bbox=[0, 0, 10, 10], confidence=0.8, class_id=1, label="cup")
        assert d.bbox == [0, 0, 10, 10]
        assert d.label == "cup"


# ---------------------------------------------------------------------------
# Tracker
# ---------------------------------------------------------------------------


class TestTracker:
    def _make_detection(self, x1, y1, x2, y2, label="obj"):
        return Detection(bbox=[x1, y1, x2, y2], confidence=0.9, class_id=0, label=label)

    def test_new_tracker_is_empty(self):
        tracker = Tracker()
        result = tracker.update([])
        assert result == []

    def test_registers_new_objects(self):
        tracker = Tracker()
        dets = [self._make_detection(0, 0, 10, 10)]
        tracked = tracker.update(dets)
        assert len(tracked) == 1
        assert tracked[0].track_id == 0
        assert tracked[0].label == "obj"

    def test_assigns_persistent_id_across_frames(self):
        tracker = Tracker()
        dets = [self._make_detection(0, 0, 10, 10)]
        first = tracker.update(dets)[0]
        # Move detection slightly
        dets2 = [self._make_detection(2, 2, 12, 12)]
        second = tracker.update(dets2)[0]
        assert first.track_id == second.track_id

    def test_removes_disappeared_objects(self):
        tracker = Tracker(max_disappeared=2)
        dets = [self._make_detection(0, 0, 10, 10)]
        tracker.update(dets)

        # No detections for 3 frames → object should be removed
        for _ in range(3):
            result = tracker.update([])

        assert result == []

    def test_object_survives_exactly_max_disappeared_frames(self):
        """Object should NOT be removed after exactly max_disappeared absent frames."""
        tracker = Tracker(max_disappeared=2)
        dets = [self._make_detection(0, 0, 10, 10)]
        tracker.update(dets)

        # Absent for exactly max_disappeared (2) frames → still tracked
        for _ in range(2):
            result = tracker.update([])
        assert len(result) == 1

        # One more absent frame (total = max_disappeared + 1 = 3) → removed
        result = tracker.update([])
        assert result == []

    def test_reset_clears_all_tracks(self):
        tracker = Tracker()
        tracker.update([self._make_detection(0, 0, 10, 10)])
        tracker.reset()
        assert tracker.update([]) == []

    def test_multiple_objects_get_unique_ids(self):
        tracker = Tracker()
        dets = [
            self._make_detection(0, 0, 10, 10, "a"),
            self._make_detection(200, 200, 210, 210, "b"),
        ]
        tracked = tracker.update(dets)
        ids = {t.track_id for t in tracked}
        assert len(ids) == 2


# ---------------------------------------------------------------------------
# image_utils
# ---------------------------------------------------------------------------


class TestImageUtils:
    def test_bgr_to_rgb_swaps_channels(self):
        frame = np.zeros((4, 4, 3), dtype=np.uint8)
        frame[:, :, 0] = 10  # B
        frame[:, :, 1] = 20  # G
        frame[:, :, 2] = 30  # R
        rgb = bgr_to_rgb(frame)
        assert rgb[0, 0, 0] == 30  # was R
        assert rgb[0, 0, 2] == 10  # was B

    def test_normalize_range(self):
        frame = np.full((4, 4, 3), 255, dtype=np.uint8)
        normalized = normalize(frame)
        assert normalized.dtype == np.float32
        assert normalized.max() == pytest.approx(1.0)

    def test_normalize_zeros(self):
        frame = np.zeros((4, 4, 3), dtype=np.uint8)
        normalized = normalize(frame)
        assert normalized.min() == pytest.approx(0.0)

    def test_resize_frame(self):
        import sys
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        expected = np.zeros((224, 224, 3), dtype=np.uint8)
        mock_cv2 = MagicMock()
        mock_cv2.resize.return_value = expected
        mock_cv2.INTER_LINEAR = 1
        with patch.dict(sys.modules, {"cv2": mock_cv2}):
            result = resize_frame(frame, 224, 224)
        assert result.shape == (224, 224, 3)
