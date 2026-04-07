from constants import BeanStates
from entities import Bean


def filter_results(results):
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
    # Creacion de mascaras para granos maduros, sobremaduros e inmaduros
    isUnripe = boxes[:, 5] == 0
    isRipe = boxes[:, 5] == 1
    isOverripe = boxes[:, 5] == 2
    # Filtrado aplicando las mascaras
    ripes = boxes[isRipe].cpu().numpy()
    unripes = boxes[isUnripe].cpu().numpy()
    overripes = boxes[isOverripe].cpu().numpy()

    # Crear entidades -> Entidad([x1,y1,x2,y2], conf)
    mappedBeans = []

    for box in ripes:
        bean = Bean(box[:4], box[4])
        bean.state = BeanStates.RIPE
        mappedBeans.append(bean)

    for box in overripes:
        bean = Bean(box[:4], box[4])
        bean.state = BeanStates.OVERRIPE
        mappedBeans.append(bean)

    return mappedBeans
