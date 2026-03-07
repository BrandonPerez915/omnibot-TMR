import cv2 as cv
import numpy as np

# 0: Amarillo
# 1: Naranja
# 2: Rojo
# 3: Verde
# 4: Azul
# 5: Negro
upperColors = [] # Rango alto de colores (con buena iluminacion)
lowerColors = [] # Rango bajo de colores (sin mucha iluminacion)

def captureUpperHSV(event, x, y, _flags, _param):
    if event == cv.EVENT_LBUTTONDOWN:

        pixelRGB = frame[y, x]
        pixelHSV = cv.cvtColor(
            np.uint8([[pixelRGB]]),
            cv.COLOR_BGR2HSV
        )[0][0]

        upperColors.append(pixelHSV)

        print(f'Click {len(upperColors)} registrado')

def captureLowerHSV(event, x, y, _flags, _param):
    if event == cv.EVENT_LBUTTONDOWN:

        pixelRGB = frame[y, x]
        pixelHSV = cv.cvtColor(
            np.uint8([[pixelRGB]]),
            cv.COLOR_BGR2HSV
        )[0][0]

        lowerColors.append(pixelHSV)

        print(f'Click {len(lowerColors)} registrado')


# Cargar la imagen
upperImgPath = 'img2.jpeg'
lowerImgPath = 'img2.jpeg'
frame = cv.imread(upperImgPath)

if frame is None:
    print("No se pudo cargar la imagen")
else:
    # Inicio de calibracion para colores superiores
    cv.namedWindow('Calibración de Colores')
    cv.setMouseCallback('Calibración de Colores', captureUpperHSV)

    print(
        '''Click en cada color en el orden:
        \n0: Amarillo
        \n1: Naranja
        \n2: Rojo
        \n3: Verde
        \n4: Azul
        \n5: Negro\n'''
    )

    while True:
        cv.imshow('Calibración de Colores', frame)

        if cv.waitKey(1) & 0xFF == 27 or len(upperColors) == 6:
            break

    cv.destroyAllWindows()

    # Inicio de calibracion para colores inferiores
    cv.namedWindow('Calibración de Colores')
    cv.setMouseCallback('Calibración de Colores', captureLowerHSV)

    print(
        '''Click en cada color en el orden:
        \n0: Amarillo
        \n1: Naranja
        \n2: Rojo
        \n3: Verde
        \n4: Azul
        \n5: Negro\n'''
    )

    while True:
        cv.imshow('Calibración de Colores', frame)

        if cv.waitKey(1) & 0xFF == 27 or len(lowerColors) == 6:
            break

    cv.destroyAllWindows()

    print('\nCalibracion de colores superiores obtenida:')
    for h, s, v in upperColors:
        print(f'[{h}, {s}, {v}]', end=', ')
    print()

    print('\nCalibracion de colores inferiores obtenida:')
    for h, s, v in lowerColors:
        print(f'[{h}, {s}, {v}]', end=', ')
    print()
