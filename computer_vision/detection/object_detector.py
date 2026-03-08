"""Object detector wrapper around a YOLO-based model."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import numpy as np


@dataclass
class Detection:
    """Single detection result.

    Attributes:
        bbox:       Bounding box as [x1, y1, x2, y2] in pixel coordinates.
        confidence: Detection confidence score in [0, 1].
        class_id:   Integer class identifier.
        label:      Human-readable class label.
    """

    bbox: List[float]
    confidence: float
    class_id: int
    label: str = ""


class ObjectDetector:
    """Wraps a YOLO model for frame-by-frame object detection.

    Args:
        model_path: Path to the YOLO weights file (.pt / .onnx).
        confidence_threshold: Minimum confidence to accept a detection.
        device: Inference device, e.g. ``"cpu"`` or ``"cuda:0"``.
    """

    def __init__(
        self,
        model_path: str,
        confidence_threshold: float = 0.5,
        device: str = "cpu",
    ) -> None:
        self.model_path = Path(model_path)
        self.confidence_threshold = confidence_threshold
        self.device = device
        self._model = None  # Lazy-loaded on first call to detect()

    def _load_model(self) -> None:
        """Load the YOLO model (lazy initialisation)."""
        try:
            from ultralytics import YOLO  # type: ignore

            self._model = YOLO(str(self.model_path))
        except ImportError as exc:
            raise RuntimeError(
                "ultralytics is required for ObjectDetector. "
                "Install it with: pip install ultralytics"
            ) from exc

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """Run inference on a single BGR frame.

        Args:
            frame: A NumPy array with shape ``(H, W, 3)`` in BGR format.

        Returns:
            List of :class:`Detection` instances above the confidence threshold.
        """
        if self._model is None:
            self._load_model()

        results = self._model(frame, conf=self.confidence_threshold, device=self.device)
        detections: List[Detection] = []

        for result in results:
            for box in result.boxes:
                xyxy = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                label = result.names.get(cls_id, str(cls_id))
                detections.append(
                    Detection(bbox=xyxy, confidence=conf, class_id=cls_id, label=label)
                )

        return detections
