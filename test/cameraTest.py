from ultralytics import YOLO
import cv2 as cv
import numpy as np

from utils.beans import getBeanColor, getBeanLabel

MODEL_PATH = "../model/model.pt"  # Ruta al modelo entrenado
IMG_PATH = "../data/test/img3.jpeg"  # Ruta a la imagen de prueba

model = YOLO(MODEL_PATH)
cap = cv.VideoCapture(0)

# Configuracion para el video procesado
frameWidth = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
frameHeight = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))
fps = 20

fourcc = cv.VideoWriter_fourcc(*"mp4v")  # Codec para video MP4
out = cv.VideoWriter("VideoTest.mp4", fourcc, fps, (frameWidth, frameHeight))

while True:
    ret, frame = cap.read()
    if not ret:
        print("No se pudo capturar el video")
        break

    # Listas para almacenar las coordenadas de los bounding boxes de arboles y granos
    trees = []
    beans = []

    result = model.predict(frame, conf=0.5, verbose=False)[0]

    for box in result.boxes:
        boxShape = box.xyxy[0]
        classId = int(box.cls)
        className = result.names[classId]

        mappedBoxShape = (
            int(boxShape[0]),
            int(boxShape[1]),
            int(boxShape[2]),
            int(boxShape[3]),
        )

        if className == "bean":
            beans.append(mappedBoxShape)
        else:
            trees.append(mappedBoxShape)

    for beanBox in beans:
        cv.rectangle(
            frame, (beanBox[0], beanBox[1]), (beanBox[2], beanBox[3]), (0, 255, 0), 2
        )

        try:
            beanColor = getBeanColor(frame, beanBox)
            beanLabel = getBeanLabel(beanColor)

            cv.putText(
                frame,
                beanLabel,
                (beanBox[0], beanBox[1] - 10),
                cv.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 255, 0),
                2,
            )
        except Exception as e:
            print(f"Error procesando color: {e}")

    for treeBox in trees:
        cv.rectangle(
            frame, (treeBox[0], treeBox[1]), (treeBox[2], treeBox[3]), (255, 0, 0), 2
        )
        cv.putText(
            frame,
            "Tree",
            (treeBox[0], treeBox[1] - 10),
            cv.FONT_HERSHEY_SIMPLEX,
            0.9,
            (255, 0, 0),
            2,
        )

    out.write(frame)
    cv.imshow("Video", frame)

    if cv.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
out.release()
cv.destroyAllWindows()
