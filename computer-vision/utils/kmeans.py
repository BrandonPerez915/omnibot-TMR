import numpy as np

CLUSTERS = 6
MAX_ITER = 100
TOLERANCE = 1e-4


def kmeans(data):
    if len(data) < CLUSTERS:
        return np.zeros((CLUSTERS, 2)), np.zeros(len(data))

    # Normalización Min-Max
    dataMin = data.min(axis=0)
    dataMax = data.max(axis=0)

    # Si max - min == 0 entonces el denominador se vuelve 1 para evitar división por cero
    denominator = np.where((dataMax - dataMin) == 0, 1, dataMax - dataMin)
    normalizedData = (data - dataMin) / denominator

    # Kmeans++
    normalizedCentroids = [normalizedData[np.random.randint(len(normalizedData))]]
    for _ in range(1, CLUSTERS):
        squaredDistances = np.array(
            [
                min([np.inner(c - x, c - x) for c in normalizedCentroids])
                for x in normalizedData
            ]
        )

        probs = squaredDistances / squaredDistances.sum()
        cumulativeProbs = probs.cumsum()
        r = np.random.rand()

        for j, p in enumerate(cumulativeProbs):
            if r < p:
                normalizedCentroids.append(normalizedData[j])
                break
    normalizedCentroids = np.array(normalizedCentroids)

    for _ in range(MAX_ITER):
        # Distancia euclidiana sobre datos normalizados
        distances = np.linalg.norm(
            normalizedData[:, np.newaxis] - normalizedCentroids, axis=2
        )
        closestCentroid = np.argmin(distances, axis=1)
        newCentroids = np.zeros_like(normalizedCentroids)

        for k in range(CLUSTERS):
            pointsInCluster = normalizedData[closestCentroid == k]

            if len(pointsInCluster) > 0:
                newCentroids[k] = pointsInCluster.mean(axis=0)
            else:
                newCentroids[k] = normalizedData[np.random.randint(len(normalizedData))]

        if np.all(np.abs(normalizedCentroids - newCentroids) < TOLERANCE):
            break

        normalizedCentroids = newCentroids

    # Denormalización de los centroides
    finalCentroids = (normalizedCentroids * denominator) + dataMin

    return finalCentroids, closestCentroid
