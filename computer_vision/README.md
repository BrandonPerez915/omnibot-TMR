# computer_vision/

Computer vision sub-system for the omnibot-TMR.

## Sub-packages

| Package | Description |
|---------|-------------|
| `detection/` | Object detection using a YOLO-based model |
| `tracking/` | Multi-object tracking (e.g., SORT / DeepSORT) |
| `utils/` | Image pre/post-processing helpers |

## Usage

```python
from computer_vision.detection.object_detector import ObjectDetector
from computer_vision.tracking.tracker import Tracker

detector = ObjectDetector(model_path="config/model.pt")
tracker  = Tracker()

detections     = detector.detect(frame)
tracked_objects = tracker.update(detections)
```
