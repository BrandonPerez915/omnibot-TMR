import spidev
import time

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1000000
spi.mode = 0

def sendCommand(cmd):
    # Convertimos el caracter a su valor ASCII
    cmd_byte = ord(cmd[0])
    
    # Mandamos exactamente 4 bytes: La letra y 3 espacios vacios
    # Esto asegura que el DMA de la ESP32 no se trabe
    spi.xfer2([cmd_byte, 0, 0, 0])
    print("Comando enviado: " + cmd)

# if __name__ == "__main__":
#     print("Controlador de Navegacion Iniciado.")
#     print("Escribe una letra (E, S, R, A, P, F, O) y presiona Enter:")
    
#     try:
#         while True:
#             comando = input("> ")
#             if len(comando) > 0:
#                 # Convertimos a mayuscula por seguridad
#                 enviar_comando(comando.upper())
                
#     except KeyboardInterrupt:
#         spi.close()
#         print("\nConexion cerrada")