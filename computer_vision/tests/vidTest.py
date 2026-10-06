from ultralytics import YOLO
import cv2 as cv

from computer_vision.utils.results import filter_results

MODEL_PATH = "./model/model.pt"

model = YOLO(MODEL_PATH)
cap = cv.VideoCapture(1)

while True:
    ret, frame = cap.read()

    if not ret:
        break

    # Dibujar box en el centro del frame
    cv.rectangle(
        frame,
        (frame.shape[1] // 2 - 100, frame.shape[0] // 2 - 100),
        (frame.shape[1] // 2 + 100, frame.shape[0] // 2 + 100),
        (255, 255, 255),
        2,
    )

    rawResults = model.predict(frame, conf=0.5, verbose=False)[0]
    data = filter_results(rawResults, frame)

    for bean in data["beans"]:
        color = None
        if bean.colorName == "Sobremaduro":
            color = (0, 0, 0)
        elif bean.colorName == "Maduro":
            color = (0, 0, 255)
        else:
            color = (0, 255, 0)

        cv.rectangle(frame, (bean.x1, bean.y1), (bean.x2, bean.y2), color, 2)
        label_text = bean.colorName
        cv.putText(
            frame,
            label_text,
            (bean.x1, bean.y1 - 10),
            cv.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2,
        )

    # for tree in data["trees"]:
    #     cv.rectangle(frame, (tree.x1, tree.y1), (tree.x2, tree.y2), (255, 0, 0), 2)

    # Verificar si hay granos dentro del box central
    central_box = {
        "x1": frame.shape[1] // 2 - 100,
        "y1": frame.shape[0] // 2 - 100,
        "x2": frame.shape[1] // 2 + 100,
        "y2": frame.shape[0] // 2 + 100,
    }
    for bean in data["beans"]:
        if (
            bean.x1 >= central_box["x1"]
            and bean.y1 >= central_box["y1"]
            and bean.x2 <= central_box["x2"]
            and bean.y2 <= central_box["y2"]
        ):
            print(f"Grano detectado dentro del box central: {bean.colorName}")

    cv.imshow("Result", frame)
    if cv.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv.destroyAllWindows()
