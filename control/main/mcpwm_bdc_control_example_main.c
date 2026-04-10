#include "robot_config.h"
#include "motors.h"
#include "sensors.h"
#include "comms.h"
#include "navigation.h"

void app_main(void) {
    ESP_LOGI("MAIN", "Iniciando sistema del Robot Omnidireccional...");

    // 1. INICIALIZAR COMUNICACIONES (SPI SLAVE)
    init_comms();

    // 2. Inicializar Sensores (I2C, MPU9250, ADC1, TCRT5000)
    init_sensors();

    // 3. Inicializar Hardware de Motores (Pines, LEDC, MCPWM, PID)
    init_motors();

    // 4. Iniciar Cerebro de Navegacion (Cinematica y Seguidor de linea)
    init_navigation();

    ESP_LOGI("MAIN", "Inicializacion completada con exito.");
}