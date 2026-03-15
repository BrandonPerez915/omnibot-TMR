from ultralytics import YOLO
import cv2 as cv
from utils.results import filterResults

MODEL_PATH = "./model/model.pt"
CONF_LEVEL = 0.1

model = YOLO(MODEL_PATH)

cap = cv.VideoCapture(0)

cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    rawResults = model.predict(frame, conf=CONF_LEVEL, verbose=False)[0]

    data = filterResults(rawResults)

    for tree in data["trees"]:
        cv.rectangle(frame, (tree.x1, tree.y1), (tree.x2, tree.y2), (255, 0, 0), 2)
        cv.putText(
            frame,
            f"T ({tree.confidence:.2f})",
            (tree.x1, tree.y1 - 7),
            cv.FONT_HERSHEY_SIMPLEX,
            0.4,
            (255, 0, 0),
            1,
            cv.LINE_AA,
        )

    for bean in data["beans"]:
        cv.rectangle(frame, (bean.x1, bean.y1), (bean.x2, bean.y2), (0, 255, 0), 1)
        name = getattr(bean, "colorName", "B")
        cv.putText(
            frame,
            name,
            (bean.x1, bean.y1 - 5),
            cv.FONT_HERSHEY_SIMPLEX,
            0.3,
            (0, 255, 0),
            1,
            cv.LINE_AA,
        )

    cv.imshow("Omnibot", frame)
    if cv.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv.destroyAllWindows()
