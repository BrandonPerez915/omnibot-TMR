"""Simple centroid-based multi-object tracker."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import numpy as np

from computer_vision.detection.object_detector import Detection


@dataclass
class TrackedObject:
    """A detection enriched with a persistent tracking ID.

    Attributes:
        track_id:   Unique integer ID assigned by the tracker.
        bbox:       Current bounding box as [x1, y1, x2, y2].
        confidence: Detection confidence from the latest frame.
        class_id:   Class identifier.
        label:      Human-readable class label.
        centroid:   (cx, cy) centre of the bounding box.
        age:        Number of consecutive frames the object has been tracked.
    """

    track_id: int
    bbox: List[float]
    confidence: float
    class_id: int
    label: str
    centroid: Tuple[float, float] = field(default=(0.0, 0.0))
    age: int = 1


class Tracker:
    """Centroid-based tracker that assigns persistent IDs across frames.

    Args:
        max_disappeared: Frames an object can be absent before it is removed.
        max_distance:    Maximum pixel distance to associate a detection with a
                         known track.
    """

    def __init__(self, max_disappeared: int = 10, max_distance: float = 80.0) -> None:
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance

        self._next_id: int = 0
        self._tracks: Dict[int, TrackedObject] = {}
        self._disappeared: Dict[int, int] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(self, detections: List[Detection]) -> List[TrackedObject]:
        """Update the tracker with new detections and return current tracks.

        Args:
            detections: Detections from the current frame.

        Returns:
            List of :class:`TrackedObject` instances for the current frame.
        """
        if not detections:
            self._handle_no_detections()
            return list(self._tracks.values())

        det_centroids = [self._centroid(d.bbox) for d in detections]

        if not self._tracks:
            for i, det in enumerate(detections):
                self._register(det, det_centroids[i])
        else:
            self._match_and_update(detections, det_centroids)

        return list(self._tracks.values())

    def reset(self) -> None:
        """Clear all tracks."""
        self._tracks.clear()
        self._disappeared.clear()
        self._next_id = 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _centroid(bbox: List[float]) -> Tuple[float, float]:
        return ((bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0)

    def _register(self, det: Detection, centroid: Tuple[float, float]) -> None:
        track_id = self._next_id
        self._next_id += 1
        self._tracks[track_id] = TrackedObject(
            track_id=track_id,
            bbox=det.bbox,
            confidence=det.confidence,
            class_id=det.class_id,
            label=det.label,
            centroid=centroid,
        )
        self._disappeared[track_id] = 0

    def _deregister(self, track_id: int) -> None:
        del self._tracks[track_id]
        del self._disappeared[track_id]

    def _handle_no_detections(self) -> None:
        for track_id in list(self._disappeared.keys()):
            self._disappeared[track_id] += 1
            if self._disappeared[track_id] > self.max_disappeared:
                self._deregister(track_id)

    def _match_and_update(
        self,
        detections: List[Detection],
        det_centroids: List[Tuple[float, float]],
    ) -> None:
        track_ids = list(self._tracks.keys())
        track_centroids = [self._tracks[tid].centroid for tid in track_ids]

        # Build distance matrix (tracks × detections)
        dist_matrix = np.zeros((len(track_ids), len(det_centroids)), dtype=float)
        for r, tc in enumerate(track_centroids):
            for c, dc in enumerate(det_centroids):
                dist_matrix[r, c] = np.linalg.norm(np.array(tc) - np.array(dc))

        # Greedy matching: match closest pairs first
        matched_tracks = set()
        matched_dets = set()

        rows = dist_matrix.min(axis=1).argsort()
        for r in rows:
            c = int(dist_matrix[r].argmin())
            if r in matched_tracks or c in matched_dets:
                continue
            if dist_matrix[r, c] > self.max_distance:
                continue
            tid = track_ids[r]
            det = detections[c]
            obj = self._tracks[tid]
            obj.bbox = det.bbox
            obj.confidence = det.confidence
            obj.centroid = det_centroids[c]
            obj.age += 1
            self._disappeared[tid] = 0
            matched_tracks.add(r)
            matched_dets.add(c)

        # Handle unmatched tracks
        for r, tid in enumerate(track_ids):
            if r not in matched_tracks:
                self._disappeared[tid] += 1
                if self._disappeared[tid] > self.max_disappeared:
                    self._deregister(tid)

        # Register new detections
        for c, det in enumerate(detections):
            if c not in matched_dets:
                self._register(det, det_centroids[c])
