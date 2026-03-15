from ultralytics import YOLO
import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.colors as mcolors

from utils.results import filterResults
from utils.kmeans import kmeans

MODEL_PATH = "./model/model.pt"  # Ruta al modelo entrenado
IMG_PATH = "../data/test/img3.jpeg"  # Ruta a la imagen de prueba

model = YOLO(MODEL_PATH)

rawResults = model.predict(IMG_PATH, conf=0.5)[0]
# Filtrado y agrupamiento personalizado a las entidades Bean y Tree
data = filterResults(rawResults)

img = cv.imread(IMG_PATH)

for bean in data["beans"]:
    bean.setHSV(img)
    cv.rectangle(
        img,
        (bean.x1, bean.y1),
        (bean.x2, bean.y2),
        (0, 255, 0),
        2,
    )
    cv.putText(
        img,
        bean.colorName if bean.colorName else "bean" + f" ({bean.confidence:.2f})",
        (bean.x1, bean.y1 - 10),
        cv.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 0),
        1,
    )

for tree in data["trees"]:
    cv.rectangle(
        img,
        (tree.x1, tree.y1),
        (tree.x2, tree.y2),
        (255, 0, 0),
        2,
    )
    cv.putText(
        img,
        "tree" + f" ({tree.confidence:.2f})",
        (tree.x1, tree.y1 - 10),
        cv.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 0, 0),
        1,
    )

if len(data["beans"]) > 0:
    hs = np.array([[bean.h, bean.s] for bean in data["beans"]])

    h_norm = hs[:, 0] / 179.0
    s_norm = hs[:, 1] / 255.0
    v_norm = np.ones_like(h_norm) * 0.8  # Brillo constante al 80%

    hsv_stack = np.stack([h_norm, s_norm, v_norm], axis=1)
    rgb_colors = mcolors.hsv_to_rgb(hsv_stack)
else:
    hs = np.empty((0, 2))
    rgb_colors = []

centroids, closestCentroid = kmeans(hs)

plt.figure(figsize=(10, 6))

if len(hs) > 0:
    plt.scatter(
        hs[:, 0],
        hs[:, 1],
        c=rgb_colors,
        edgecolors="black",
        linewidth=0.5,
        s=50,
        alpha=0.9,
    )

ax = plt.gca()
for x, y in centroids:
    padding_x = 10  # Padding para Hue
    padding_y = 10  # Padding para Saturation

    rect = patches.Rectangle(
        (x - padding_x, y - padding_y),
        padding_x * 2,  # Ancho total
        padding_y * 2,  # Alto total
        linewidth=1.5,
        edgecolor="red",
        facecolor="none",
        linestyle="--",
    )
    ax.add_patch(rect)

plt.xlabel("Hue (Matiz)")
plt.ylabel("Saturation (Saturación)")
plt.title("Visualización Real de Colores y Clusters K-means")
plt.legend()
plt.grid(True, alpha=0.2)
plt.show()
