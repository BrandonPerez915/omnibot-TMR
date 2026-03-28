from ultralytics import YOLO
import cv2 as cv
import matplotlib.pyplot as plt
from utils.results import filterResults

MODEL_PATH = "./model/model.engine" 
IMG_PATH = "../dataset/img2.jpg"

model = YOLO(MODEL_PATH, task='detect')

rawResults = model.predict(IMG_PATH, conf=0.5, device=0)[0]
img = cv.imread(IMG_PATH)
data = filterResults(rawResults, img)

l_vals, a_vals, b_vals, colors = [], [], [], []

for bean in data["beans"]:
    l_vals.append(bean.l)
    a_vals.append(bean.a)
    b_vals.append(bean.b)

    if bean.colorName == "Sobremaduro":
        draw_color = (0, 0, 0)      # BGR para OpenCV
        plot_color = (0, 0, 0)      # RGB para Plot
    elif bean.colorName == "Maduro":
        draw_color = (255, 0, 0)    # BGR (Azul)
        plot_color = (0, 0, 1)      # RGB (Azul)
    else:
        draw_color = (0, 255, 0)    # BGR (Verde)
        plot_color = (0, 1, 0)      # RGB (Verde)

    colors.append(plot_color)
    
    cv.rectangle(img, (bean.x1, bean.y1), (bean.x2, bean.y2), draw_color, 2)
    cv.putText(img, bean.colorName, (bean.x1, bean.y1 - 10), 
               cv.FONT_HERSHEY_SIMPLEX, 0.5, draw_color, 2)

fig = plt.figure(figsize=(15, 7))

ax_img = fig.add_subplot(1, 2, 1)
img_rgb = cv.cvtColor(img, cv.COLOR_BGR2RGB)
ax_img.imshow(img_rgb)
ax_img.set_title("Detecciones YOLO")
ax_img.axis("off") 

ax_3d = fig.add_subplot(1, 2, 2, projection="3d")

if len(data["beans"]) > 0:
    ax_3d.scatter(a_vals, b_vals, l_vals, c=colors, s=60, edgecolors="k")
    ax_3d.set_xlabel("Canal a")
    ax_3d.set_ylabel("Canal b")
    ax_3d.set_zlabel("Luminosidad (L)")
    ax_3d.set_title("Espacio de Color LAB")

plt.tight_layout()
plt.show()
