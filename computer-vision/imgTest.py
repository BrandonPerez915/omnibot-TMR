from ultralytics import YOLO
import cv2 as cv

from utils.results import filterResults


MODEL_PATH = "./model/model.pt"
IMG_PATH = "../data/test/img5.png"

model = YOLO(MODEL_PATH)
rawResults = model.predict(IMG_PATH, conf=0.5)[0]

img = cv.imread(IMG_PATH)
data = filterResults(rawResults, img)

for bean in data["beans"]:
    color = None
    if bean.colorName == "Sobremaduro":
        color = (0, 0, 0)
    elif bean.colorName == "Maduro":
        color = (0, 0, 255)
    else:
        color = (0, 255, 0)

    cv.rectangle(img, (bean.x1, bean.y1), (bean.x2, bean.y2), color, 2)
    label_text = bean.colorName
    cv.putText(
        img,
        label_text,
        (bean.x1, bean.y1 - 10),
        cv.FONT_HERSHEY_SIMPLEX,
        0.5,
        color,
        2,
    )

for tree in data["trees"]:
    cv.rectangle(img, (tree.x1, tree.y1), (tree.x2, tree.y2), (255, 0, 0), 2)

# # Configurar la gráfica 3D
# fig = plt.figure(figsize=(10, 7))
# ax = fig.add_subplot(111, projection="3d")

# l_vals, a_vals, b_vals, colors = [], [], [], []

# if len(data["beans"]) > 0:
#     ax.scatter(a_vals, b_vals, l_vals, c=colors, s=60, edgecolors="k")
#     ax.set_xlabel("Canal a (Verde <-> Rojo)")
#     ax.set_ylabel("Canal b (Azul <-> Amarillo)")
#     ax.set_zlabel("Canal L (Luminosidad)")
#     ax.set_title("Distribución de Granos en Espacio LAB")
#     plt.show()

cv.imshow("Result", img)
cv.waitKey(0)
cv.destroyAllWindows()
