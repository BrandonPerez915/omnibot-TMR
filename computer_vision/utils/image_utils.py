"""Image pre- and post-processing utilities for the computer vision pipeline."""

from __future__ import annotations

from typing import Tuple

import numpy as np


def resize_frame(
    frame: np.ndarray, width: int, height: int
) -> np.ndarray:
    """Resize a frame to the given dimensions.

    Args:
        frame:  Input image as a NumPy array (H, W, C).
        width:  Target width in pixels.
        height: Target height in pixels.

    Returns:
        Resized image array.
    """
    import cv2  # type: ignore

    return cv2.resize(frame, (width, height), interpolation=cv2.INTER_LINEAR)


def bgr_to_rgb(frame: np.ndarray) -> np.ndarray:
    """Convert a BGR frame to RGB.

    Args:
        frame: Input image in BGR format.

    Returns:
        Image in RGB format.
    """
    return frame[:, :, ::-1].copy()


def draw_detections(
    frame: np.ndarray,
    detections: list,
    color: Tuple[int, int, int] = (0, 255, 0),
    thickness: int = 2,
) -> np.ndarray:
    """Draw bounding boxes and labels on a frame.

    Args:
        frame:      BGR image to annotate (modified in-place).
        detections: List of objects with ``bbox`` and ``label`` attributes.
        color:      BGR colour for the bounding boxes.
        thickness:  Line thickness in pixels.

    Returns:
        Annotated frame (same array as input).
    """
    import cv2  # type: ignore

    for det in detections:
        x1, y1, x2, y2 = [int(v) for v in det.bbox]
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
        label = getattr(det, "label", "")
        if label:
            cv2.putText(
                frame,
                label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                thickness,
            )
    return frame


def normalize(frame: np.ndarray) -> np.ndarray:
    """Normalize pixel values to [0, 1].

    Args:
        frame: Input image array with dtype uint8.

    Returns:
        Float32 array with values in [0.0, 1.0].
    """
    return frame.astype(np.float32) / 255.0
