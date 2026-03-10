from ultralytics import YOLO
import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt

from utils.beans import getBeanColor, getBeanLabel

# Informacion sobre la clase Results de Ultralytics YOLOv8:

# Attributes:
#     orig_img (np.ndarray): The original image as a numpy array.
#     orig_shape (tuple[int, int]): Original image shape in (height, width) format.
#     boxes (Boxes | None): Detected bounding boxes.
#     masks (Masks | None): Segmentation masks.
#     probs (Probs | None): Classification probabilities.
#     keypoints (Keypoints | None): Detected keypoints.
#     obb (OBB | None): Oriented bounding boxes.
#     speed (dict): Dictionary containing inference speed information.
#     names (dict): Dictionary mapping class indices to class names.
#     path (str): Path to the input image file.
#     save_dir (str | None): Directory to save results.

# Methods:
#     update: Update the Results object with new detection data.
#     cpu: Return a copy of the Results object with all tensors moved to CPU memory.
#     numpy: Convert all tensors in the Results object to numpy arrays.
#     cuda: Move all tensors in the Results object to GPU memory.
#     to: Move all tensors to the specified device and dtype.
#     new: Create a new Results object with the same image, path, names, and speed attributes.
#     plot: Plot detection results on an input BGR image.
#     show: Display the image with annotated inference results.
#     save: Save annotated inference results image to file.
#     verbose: Return a log string for each task in the results.
#     save_txt: Save detection results to a text file.
#     save_crop: Save cropped detection images to specified directory.
#     summary: Convert inference results to a summarized dictionary.
#     to_df: Convert detection results to a Polars DataFrame.
#     to_json: Convert detection results to JSON format.
#     to_csv: Convert detection results to a CSV format.

MODEL_PATH = "../model/model.pt"  # Ruta al modelo entrenado
IMG_PATH = "../data/test/img3.jpeg"  # Ruta a la imagen de prueba

model = YOLO(MODEL_PATH)
result = model.predict(IMG_PATH, conf=0.5)[0]  # save=True para guardar en runs/detect/

trees = []
beans = []

for box in result.boxes:
    boxShape = (
        box.xyxy
    )  # Coordenadas del bounding box en formato (x1, y1, x2, y2) -> np.ndarray

    classId = int(box.cls)  # ID de la clase detectada -> tensor de un valor
    className = result.names[classId]  # Nombre de la clase detectada -> dict[int, str]

    mappedBoxShape = (
        int(boxShape[0][0]),
        int(boxShape[0][1]),
        int(boxShape[0][2]),
        int(boxShape[0][3]),
    )

    if className == "bean":
        beans.append(mappedBoxShape)
    else:
        trees.append(mappedBoxShape)

print(f"Trees detected: {len(trees)}")
print(trees)
print(f"Beans detected: {len(beans)}")
print(beans)

img = cv.imread(IMG_PATH)
hsvData = []

for beanBox in beans:
    cv.rectangle(
        img, (beanBox[0], beanBox[1]), (beanBox[2], beanBox[3]), (255, 0, 0), 3
    )

    beanColor = getBeanColor(result.orig_img, beanBox)
    h, s, v = beanColor
    hsvData.append((h, s, v))
    colorName = getBeanLabel(beanColor)

    cv.putText(
        img,
        colorName,
        (beanBox[0] + 10, beanBox[1] + 30),
        cv.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 0, 0),
        2,
    )

if len(hsvData) > 0:
    data = np.array(hsvData)

    fig = plt.figure(figsize=(15, 6))

    # Grafica 2D
    ax1 = fig.add_subplot(1, 2, 1)
    scatter1 = ax1.scatter(
        data[:, 0], data[:, 1], c=data[:, 0], cmap="hsv", edgecolors="k"
    )
    ax1.set_title("Plano Hue-Saturation (Cromaticidad)")
    ax1.set_xlabel("Hue (Matiz)")
    ax1.set_ylabel("Saturation (Pureza)")
    ax1.grid(True)

    # Grafica 3D
    ax2 = fig.add_subplot(1, 2, 2, projection="3d")
    scatter2 = ax2.scatter(
        data[:, 0], data[:, 1], data[:, 2], c=data[:, 0], cmap="hsv", s=50
    )
    ax2.set_title("Espacio 3D HSV (Incluye Brillo)")
    ax2.set_xlabel("H")
    ax2.set_ylabel("S")
    ax2.set_zlabel("V (Brillo)")

    plt.tight_layout()
    plt.show()
else:
    print("No se detectaron granos para graficar.")

cv.imshow("Detection Result", img)
cv.waitKey(0)
# cv.imwrite('./runs/images/imageTestResult.jpeg', img) # Guardar la imagen con detecciones y colores anotados
