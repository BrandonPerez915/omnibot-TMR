import numpy as np

from entities.Tree import Tree
from entities.Bean import Bean


def filterResults(results):
    """
    Filtra árboles con confianza > 0.6 y granos que estén dentro de dichos árboles.
    Args:
        results: Objeto de resultados de detección de Ultralytics con atributos .boxes, .probs, etc.
    Returns:
        newResults: dict con claves "trees" y "beans", cada una con un np.array de objetos Tree
        o Bean respectivamente.
    """

    tempTrees = []
    tempBeans = []

    for box in results.boxes:
        classId = int(box.cls.item())
        confidence = box.conf.item()

        if classId == 1 and confidence > 0.6:
            tempTrees.append(Tree(box, confidence))
        elif classId == 0:
            tempBeans.append(Bean(box, confidence))

    validBeans = [
        bean for bean in tempBeans if any(bean.inTree(tree) for tree in tempTrees)
    ]

    return {"trees": tempTrees, "beans": validBeans}
