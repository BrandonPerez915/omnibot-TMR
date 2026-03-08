from ultralytics import YOLO
import cv2 as cv
import numpy as np
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.beans import getBeanColor

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

MODEL_PATH = '../model/model.pt' # Ruta al modelo entrenado
IMG_PATH = '../data/test/img3.jpeg' # Ruta a la imagen de prueba

model = YOLO(MODEL_PATH)
result = model.predict(IMG_PATH, conf=0.5)[0] # save=True para guardar en runs/detect/

trees = []
beans = []

for box in result.boxes:
    boxShape = box.xyxy # Coordenadas del bounding box en formato (x1, y1, x2, y2) -> np.ndarray

    classId = int(box.cls)              # ID de la clase detectada -> tensor de un valor
    className = result.names[classId]   # Nombre de la clase detectada -> dict[int, str]

    mappedBoxShape = (
        int(boxShape[0][0]), 
        int(boxShape[0][1]), 
        int(boxShape[0][2]), 
        int(boxShape[0][3])
    )

    if className == 'bean':
        beans.append(mappedBoxShape)
    else:
        trees.append(mappedBoxShape)

print(f'Trees detected: {len(trees)}')
print(trees)
print(f'Beans detected: {len(beans)}')
print(beans)

def getBeanColor(img: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    x1, y1, x2, y2 = box
    beanROI = img[y1:y2, x1:x2]

    if beanROI.size == 0:
        raise ValueError("La región de interés está vacía. Verifica las coordenadas del box.")

    averageRGB = cv.mean(beanROI)[:3]  # Obtener el color promedio (BGR)
    averageHSV = cv.cvtColor(np.uint8([[averageRGB]]), cv.COLOR_BGR2HSV)[0][0]  # Convertir a HSV

    return averageHSV

# TODO: Estos colores estan hardcodeados, lo ideal seria que se calibraran automaticamente
def getColorName(colorHSV: np.ndarray) -> str:
    h, s, v = colorHSV

    if v < 55: 
        return "Negro"

    if (h <= 10) or (h >= 160):
        return "Rojo"
    
    elif 11 <= h <= 25:
        return "Naranja"
    
    elif 26 <= h <= 35:
        return "Amarillo"
    
    elif 36 <= h <= 85:
        return "Verde"
    
    elif 86 <= h <= 130:
        return "Azul"

    return "Desconocido"

img = cv.imread(IMG_PATH)

for beanBox in beans:
    cv.rectangle(
        img,
        (beanBox[0], beanBox[1]),
        (beanBox[2], beanBox[3]),
        (255, 0, 0), 3
    )

    beanColor = getBeanColor(result.orig_img, beanBox)
    colorName = getColorName(beanColor)

    cv.putText(
        img,
        colorName,
        (beanBox[0] + 10, beanBox[1] + 30),
        cv.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 0, 0),
        2
    )

cv.imshow('Detection Result', img)
cv.imwrite('./runs/images/imageTestResult.jpeg', img) # Guardar la imagen con detecciones y colores anotados