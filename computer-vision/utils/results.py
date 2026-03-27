import numpy as np

from entities.Tree import Tree
from entities.Bean import Bean

import numpy as np

# Centroides fijos en el espacio AB
REFERENCE_COLORS_AB = np.array(
    [
        [160, 135],  # 0: Maduro
        [140, 165],  # 1: Maduro
        [120, 175],  # 2: Maduro
        [120, 120],  # 3: Sobremaduro
        [100, 140],  # 4: Inmaduro
        [128, 128],  # 5: Sobremaduro
    ],
    dtype=float,
)


def filterResults(results, frame):
    """
    Filtra árboles con confianza > 0.6 y granos que estén dentro de dichos árboles.
    Args:
        results: Objeto de resultados de detección de Ultralytics con atributos .boxes, .probs, etc.
    Returns:
        newResults: dict con claves "trees" y "beans", cada una con un np.array de objetos Tree
        o Bean respectivamente.
    """

    # Datos en crudo (matriz en crudo):
    # columna 0 = x1,
    # columna 1 = y1,
    # columna 2 = x2,
    # columna 3 = y2,
    # columna 4 = conf
    # columna 5 = cls
    boxes = results.boxes.data
    # Creacion de mascaras para arboles y granos
    isTree = (boxes[:, 5] == 1) & (boxes[:, 4] > 0.6)
    isBean = boxes[:, 5] == 0
    # Filtrado aplicando las mascaras
    treeBoxes = boxes[isTree]
    beanBoxes = boxes[isBean]

    # Copia de GPU a CPU
    treesNp = treeBoxes.cpu().numpy()
    beansNp = beanBoxes.cpu().numpy()

    # Crear entidades -> Entidad([x1,y1,x2,y2], conf)
    mappedTrees = [Tree(box[:4], box[4]) for box in treesNp]
    mappedBeans = [Bean(box[:4], box[4]) for box in beansNp]

    # if len(mappedTrees) == 0:
    #     print("Warning: There are no trees detected")
    # if len(mappedBeans) == 0:
    #     print("Warning: There are no beans detected")

    for bean in mappedBeans:
        bean.setLab(frame)

        if bean.b > 135 and bean.a > 115 and bean.l > 70:
            bean.colorName = "Maduro"

        elif bean.a < 125 and bean.l > 70:
            bean.colorName = "Inmaduro"

        else:
            bean.colorName = "Sobremaduro"

    return {"trees": mappedTrees, "beans": mappedBeans}
