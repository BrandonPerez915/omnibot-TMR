#include <stdio.h>
#include <string.h>
#include <math.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "driver/ledc.h"
#include "driver/mcpwm_cap.h"
#include "driver/gpio.h"
#include "driver/i2c_master.h"
#include "pid_ctrl.h"
#include "driver/adc.h" // LIBRERÍA PARA LEER SENSORES ANALÓGICOS

//ESP-NOW
#include "esp_wifi.h"
#include "esp_now.h"
#include "esp_netif.h"
#include "esp_mac.h"
#include "nvs_flash.h"

static const char *TAG = "ROBOT_OMNI";

#define NUM_MOTORS 4
#define ENCODER_CPR         764.3f
#define PID_LOOP_PERIOD_MS  50    
#define WHEEL_RADIUS        0.04f  
#define ROBOT_L             0.64f  

//IMU (Movimiento Normal)
#define KP_YAW              0.08f  
#define MAX_WZ              3.0f   //VELOCIDAD DE CORRECCIÓN MÁXIMA PARA GIRO 

//IMU (Exclusivo para Giros 'G')
#define KP_YAW_TURN         0.015f // Rampa de frenado larga para matar inercia
#define MAX_WZ_TURN         0.5f   // Velocidad tope controlada

// ==========================================
// SEGUIDOR DE LÍNEA (MODIFICADO PARA FLUIDEZ)
// ==========================================
#define KP_LINEA            0.3f   // REDUCIDO: Menos agresivo para no pasarse
#define KD_LINEA            0.4f   // AUMENTADO: Más freno derivativo para no oscilar
#define MAX_CORRECCION_VY   0.3f   // AUMENTADO: Le da fuerza para regresar a la línea si se sale
#define BANDA_MUERTA        0.15f  // NUEVO: Tolerancia (si el error es menor a esto, asume que está centrado)

// CALIBRACIÓN DE SENSORES TCRT5000 (Basado en lecturas reales)
#define VALOR_BLANCO        503.0f  // Promedio combinado de los sensores IZQ y DER
#define VALOR_NEGRO         616.0f  // Promedio del sensor CEN
//MPU9250 CON I2C
#define I2C_MASTER_SDA_IO   15   
#define I2C_MASTER_SCL_IO   16
#define MPU9250_ADDR        0x68
#define PWR_MGMT_1          0x6B
#define GYRO_CONFIG         0x1B
#define GYRO_ZOUT_H         0x47

volatile float target_speed_rads[NUM_MOTORS] = {0.0f, 0.0f, 0.0f, 0.0f};  

//PWM 
#define PWM_FREQUENCY       20000
#define PWM_RESOLUTION      LEDC_TIMER_10_BIT
#define PWM_MAX_DUTY        1023

//PINES 
const int motor_pwm_gpio[NUM_MOTORS] = {5, 6, 7, 8};
const int encoder_gpio[NUM_MOTORS]   = {9, 11, 12, 13};
const int motor_ina_gpio[NUM_MOTORS] = {19, 20, 21, 47}; 
const int motor_inb_gpio[NUM_MOTORS] = {41, 42, 2, 38}; // Pin 38 liberado para ADC1

//VARIABLES GLOBALES
static volatile uint32_t pulse_count[NUM_MOTORS] = {0};
static uint64_t last_eval_time[NUM_MOTORS] = {0};  //ULTIMO TIEMPO EN EL QUE SE HIZO UNA EVALUACIÓN PID PARA CADA MOTOR
static portMUX_TYPE spinlock = portMUX_INITIALIZER_UNLOCKED; //INTERRUPTOR DE HARDWARE PARA VARIABLES COMPARTIDAS ISR Y TAREAS
static float filtered_omega[NUM_MOTORS] = {0, 0, 0, 0};

volatile float current_yaw = 0.0f;
volatile float target_yaw = 0.0f;
volatile float cmd_vx = 0.0f;
volatile float cmd_vy = 0.0f;
volatile bool robot_active = false; //PARA MANDAR EL ROBOT A FRENAR CUANDO SE CUMPLA EL TIEMPO DE MOVIMIENTO 
static uint64_t movement_end_time = 0; //DURACIÓN DEL MOVIMIENTO 

// BANDERAS DE NAVEGACIÓN
volatile bool is_pure_turn = false;
volatile bool is_line_follower = false;
static float error_linea_ant = 0.0f;
// Variables para compartir datos entre ADC task y NAV timer
volatile float shared_error_linea = 0.0f; 
volatile bool shared_line_detected = false; 

typedef struct { pid_ctrl_block_handle_t pid; //MANEJO DEL CONTROLADOR PID PARA CADA MOTOR
} motor_ctx_t;

static motor_ctx_t motors[NUM_MOTORS];

typedef struct { int index;  //ÍNDICE DEL MOTOR PARA CALLBACK DE CAPTURA
} encoder_ctx_t;

static encoder_ctx_t enc_ctx[NUM_MOTORS];

i2c_master_dev_handle_t dev_handle; //CONTROLADOR DEL BUS I2C PARA LA IMU

// COMANDOS DE PC A ROBOT
typedef struct __attribute__((packed)) { //EMPAQUETADO PARA EVITAR BASURA ENVÍO DE 4 BYTES
    char cmd;        
    float vx;
    float vy;
    float target_yaw;
    int duration_ms; 
} control_cmd_t;

//COMANDOS ROBOT A ESP TELEMETRÍA
typedef struct __attribute__((packed)) { //EMPAQUETADO PARA EVITAR BASURA DE RELLENO
    float yaw;
    float omega[4];  
} telemetry_data_t;

// MAC ESP32 TELEMETRÍA
uint8_t pc_mac_address[] = {0xd0, 0xcf, 0x13, 0x0b, 0x0a, 0x9c};

/*!
 * @brief Función para mapear los valores crudos de los sensores TCRT5000 a una escala de 0 a 1000, donde 0 representa el valor de blanco (sin línea) y 1000 representa el
 * @param raw_val Valor crudo leído del ADC (0 a 4095 para resolución de 12 bits)
 * @return Valor mapeado en la escala de 0 a 1000, con
*/
float mapear_sensor(int raw_val) {
    float val = (float)raw_val;
    // Acotar límites
    if (val < VALOR_BLANCO) val = VALOR_BLANCO;
    if (val > VALOR_NEGRO) val = VALOR_NEGRO;
    
    // Regla de 3 para estirar de 0 a 1000
    return ((val - VALOR_BLANCO) * 1000.0f) / (VALOR_NEGRO - VALOR_BLANCO);
}

//CALLBACK
static bool encoder_capture_callback(mcpwm_cap_channel_handle_t cap_chan, const mcpwm_capture_event_data_t *edata, void *user_data) {
    encoder_ctx_t *ctx = (encoder_ctx_t *)user_data;
    pulse_count[ctx->index]++;
    return false;
}

void mpu9250_init_sensor() {
    uint8_t data[2];
    data[0] = PWR_MGMT_1; data[1] = 0x80; //RESET DEL SENSOR
    i2c_master_transmit(dev_handle, data, 2, -1); 
    vTaskDelay(pdMS_TO_TICKS(100));

    data[0] = PWR_MGMT_1; data[1] = 0x03; //SINRONIZACIÓN RELOJ DE GIROSCOPIO
    i2c_master_transmit(dev_handle, data, 2, -1);
    
    data[0] = GYRO_CONFIG; data[1] = 0x00; //AUMENTA LA SENSIBILIDAD DEL GIROSCOPIO A 250DPS
    i2c_master_transmit(dev_handle, data, 2, -1);
    
    ESP_LOGI(TAG, "Sensor MPU-9250 inicializado correctamente");
}

float read_gyro_z() {
    uint8_t reg = GYRO_ZOUT_H;
    uint8_t data[2] = {0, 0};
    
    esp_err_t ret = i2c_master_transmit_receive(dev_handle, &reg, 1, data, 2, -1);
    if (ret != ESP_OK) return 0.0;

    int16_t raw_z = (int16_t)((data[0] << 8) | data[1]);
    return (float)raw_z / 131.0; //POR LA CONFIGURACIÓN INICIAL CADA 131 ES UN 1 GRADO/S
}

void init_motor_gpios() { //CONFIGURA LOS PINES DEL IN A-B COMO SALIDA 
    for (int i = 0; i < NUM_MOTORS; i++) {
        gpio_reset_pin(motor_ina_gpio[i]); 
        gpio_set_direction(motor_ina_gpio[i], GPIO_MODE_OUTPUT);
        gpio_reset_pin(motor_inb_gpio[i]); 
        gpio_set_direction(motor_inb_gpio[i], GPIO_MODE_OUTPUT);
    }
}

// CINEMÁTICA INVERSA CORREGIDA (Vy = Frente/Atrás, Vx = Lateral)
void calculate_kinematics(float vx, float vy, float wz) {
    float multiplier = -1.0f / WHEEL_RADIUS;
    target_speed_rads[0] = multiplier * (1.0f * vy - 1.0f * vx + ROBOT_L * wz); 
    target_speed_rads[1] = multiplier * (1.0f * vy + 1.0f * vx + ROBOT_L * wz); 
    target_speed_rads[2] = multiplier * (1.0f * vy + 1.0f * vx - ROBOT_L * wz); 
    target_speed_rads[3] = multiplier * (1.0f * vy - 1.0f * vx - ROBOT_L * wz); 
}

// ASIGNA LOS VALORES RECIBIDOS POR ESP-NOW A LAS VARIABLES GLOBALES PARA CONTROL DE MOVIMIENTO
void on_data_recv(const esp_now_recv_info_t *esp_now_info, const uint8_t *incomingData, int len) {
    if (len == sizeof(control_cmd_t)) {
        control_cmd_t cmd;
        memcpy(&cmd, incomingData, sizeof(cmd));

        if (cmd.cmd == 'K' || cmd.cmd == 'k') {
            ESP_LOGI(TAG, "CMD Recibido: Vx:%.2f Vy:%.2f Yaw:%.2f Dur:%dms", cmd.vx, cmd.vy, cmd.target_yaw, cmd.duration_ms);
            
            cmd_vx = cmd.vx;
            cmd_vy = cmd.vy;
            target_yaw = cmd.target_yaw;
            is_pure_turn = false; // MOVIMIENTO NORMAL
            is_line_follower = false;
            movement_end_time = esp_timer_get_time() + ((uint64_t)cmd.duration_ms * 1000);
            robot_active = true;

        } else if (cmd.cmd == 'G' || cmd.cmd == 'g') {
            ESP_LOGI(TAG, "CMD Giro Relativo: %+.2f grados. Dur:%dms", cmd.target_yaw, cmd.duration_ms);
            
            cmd_vx = 0.0f; 
            cmd_vy = 0.0f;
            
            float nuevo_target = current_yaw + cmd.target_yaw;
            while (nuevo_target > 180.0f) nuevo_target -= 360.0f;
            while (nuevo_target < -180.0f) nuevo_target += 360.0f;
            
            target_yaw = nuevo_target;
            is_pure_turn = true; // MODO GIRO EXCLUSIVO
            is_line_follower = false;
            movement_end_time = esp_timer_get_time() + ((uint64_t)cmd.duration_ms * 1000);
            robot_active = true;

        } else if (cmd.cmd == 'L' || cmd.cmd == 'l') {
            ESP_LOGI(TAG, "CMD Seguidor de Linea (Cangrejo). Avance Vx:%.2f Dur:%dms", cmd.vx, cmd.duration_ms);
            
            cmd_vx = cmd.vx;     // Avance constante lateral
            cmd_vy = 0.0f;       // Vy se calculará en el PID para acercarse/alejarse de la línea
            target_yaw = current_yaw; // Bloqueamos la mirada para no rotar
            
            is_pure_turn = false;
            is_line_follower = true; // MODO SEGUIDOR ACTIVO
            error_linea_ant = 0.0f;
            movement_end_time = esp_timer_get_time() + ((uint64_t)cmd.duration_ms * 1000);
            robot_active = true;

        } else if (cmd.cmd == 'S' || cmd.cmd == 's') {
            ESP_LOGW(TAG, "COMANDO DE PARO INMEDIATO RECIBIDO");
            robot_active = false;
            is_line_follower = false;
            calculate_kinematics(0.0f, 0.0f, 0.0f);
        }
    }
}


//INICIALIZACIÓN ESP-NOW
void init_esp_now() {
    ESP_ERROR_CHECK(nvs_flash_init());
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));
    ESP_ERROR_CHECK(esp_wifi_set_storage(WIFI_STORAGE_RAM));
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_start());

    // --- FIJAR CANAL WI-FI A 1 ---
    esp_wifi_set_promiscuous(true);
    esp_wifi_set_channel(1, WIFI_SECOND_CHAN_NONE);
    esp_wifi_set_promiscuous(false);

    uint8_t mac[6];
    esp_read_mac(mac, ESP_MAC_WIFI_STA);
    ESP_LOGI(TAG, "MAC de este ROBOT: %02x:%02x:%02x:%02x:%02x:%02x", mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);

    ESP_ERROR_CHECK(esp_now_init());
    ESP_ERROR_CHECK(esp_now_register_recv_cb(on_data_recv));

    esp_now_peer_info_t peerInfo = {};
    memcpy(peerInfo.peer_addr, pc_mac_address, 6);
    peerInfo.channel = 1;  
    peerInfo.encrypt = false;
    
    if (pc_mac_address[0] != 0xFF) {
        if (esp_now_add_peer(&peerInfo) != ESP_OK){
            ESP_LOGE(TAG, "Fallo al agregar la MAC de la PC");
        }
    } else {
        ESP_LOGW(TAG, "ADVERTENCIA: No has configurado la MAC de la PC en pc_mac_address[]");
    }
}

// CONTROLADOR PID Y TELEMETRÍA
static void pid_loop_cb(void *arg) {
    uint64_t now = esp_timer_get_time();

    for (int i = 0; i < NUM_MOTORS; i++) {
        portENTER_CRITICAL_ISR(&spinlock); 
        uint32_t pulses = pulse_count[i];
        pulse_count[i] = 0;
        portEXIT_CRITICAL_ISR(&spinlock);

        float dt_sec = (now - last_eval_time[i]) / 1000000.0f;
        last_eval_time[i] = now;

        float raw_omega = 0.0f;
        if (dt_sec > 0.0f) {
            raw_omega = (pulses / ENCODER_CPR) * (2.0f * M_PI / dt_sec); // (2*pi*f)/PPR
        }

        filtered_omega[i] = (0.6f * filtered_omega[i]) + (0.4f * raw_omega); //FILTRO IIR SIMPLIFICADO
        
        float target_abs = fabs(target_speed_rads[i]); //PARA VELOCIDADES (+-)
        int dir = (target_speed_rads[i] >= 0.0f) ? 1 : 0;
        float output_pwm = 0;

        if (target_abs == 0.0f) {
            gpio_set_level(motor_ina_gpio[i], 0); gpio_set_level(motor_inb_gpio[i], 0);
            pid_compute(motors[i].pid, 0, &output_pwm); 
            output_pwm = 0; 
        } else {
            if (i == 0 || i == 1) { 
                gpio_set_level(motor_ina_gpio[i], dir == 1 ? 0 : 1);
                gpio_set_level(motor_inb_gpio[i], dir == 1 ? 1 : 0);
            } else { 
                gpio_set_level(motor_ina_gpio[i], dir == 1 ? 1 : 0);
                gpio_set_level(motor_inb_gpio[i], dir == 1 ? 0 : 1);
            }

            float error = target_abs - filtered_omega[i]; //ERROR DE VELOCIDAD DESEADA - REAL
            pid_compute(motors[i].pid, error, &output_pwm); //SE PASA A CADA MOTOR, EL ERROR EXISTENSE
                                                            //SE LE ASGINA A OUTPUT_PWM EL VALOR DE CONTROL CALCULADO POR EL PID
            if (output_pwm < 0) output_pwm = 0;
            if (output_pwm > PWM_MAX_DUTY) output_pwm = PWM_MAX_DUTY;
        }

        ledc_set_duty(LEDC_LOW_SPEED_MODE, (ledc_channel_t)i, (uint32_t)output_pwm);
        ledc_update_duty(LEDC_LOW_SPEED_MODE, (ledc_channel_t)i);
    }

    // --- ENVIAR TELEMETRÍA POR ESP-NOW ---
    if (pc_mac_address[0] != 0xFF) {
        telemetry_data_t telem;
        telem.yaw = current_yaw;
        for(int i=0; i<4; i++) telem.omega[i] = filtered_omega[i];
        
        esp_now_send(pc_mac_address, (uint8_t *) &telem, sizeof(telem));
    }
}

// -------------------------------------------------------------
// TAREA 1: IMU Y CONTROL DE ORIENTACIÓN (AHORA SOLO LEE IMU)
// -------------------------------------------------------------
void imu_heading_task(void *pvParameter) {
    float yaw = 0;
    float dt = 0.02; // 20ms
    float gyro_bias_z = 0;
    
    // Variables para el filtro
    float filtered_gz = 0;
    const float alpha = 0.15f; // Factor de suavizado (entre más cerca de 0, más suave pero más lento)

    ESP_LOGI(TAG, "ESTABILIZANDO IMU... Espera.");
    // 1. Purga inicial: descartar basura electrónica de los primeros milisegundos
    for(int i = 0; i < 100; i++) {
        read_gyro_z();
        vTaskDelay(pdMS_TO_TICKS(5));
    }

    ESP_LOGI(TAG, "CALIBRANDO IMU... NO muevas el sensor.");
    // 2. Calibración extendida para un mejor Bias
    for(int i = 0; i < 1000; i++) {
        gyro_bias_z += read_gyro_z();
        vTaskDelay(pdMS_TO_TICKS(5));
    }
    gyro_bias_z /= 1000.0;
    ESP_LOGI(TAG, "IMU Calibrada. Bias Z: %.4f", gyro_bias_z);

    while (1) {
        float raw_gz = read_gyro_z() - gyro_bias_z;

        // 3. Filtro Pasa Bajas Exponencial
        filtered_gz = (alpha * raw_gz) + ((1.0f - alpha) * filtered_gz);

        // 4. Zona muerta aplicada sobre la señal ya filtrada y un poco más alta
        if (fabs(filtered_gz) > 0.25f) { 
            yaw += filtered_gz * dt;
        }

        // Normalización de los grados
        if (yaw > 180.0f) yaw -= 360.0f;
        if (yaw < -180.0f) yaw += 360.0f;
        
        current_yaw = yaw;

        // --- IMPRESIÓN DEL YAW ACTUAL EN CONSOLA ---
        ESP_LOGI(TAG, "Yaw actual: %6.2f | GZ Filtrado: %6.2f", current_yaw, filtered_gz);

        vTaskDelay(pdMS_TO_TICKS(20));
    }
}

// -------------------------------------------------------------
// TAREA 2: LECTURA DE SENSORES ADC PARA EL SEGUIDOR DE LÍNEA
// -------------------------------------------------------------
void adc_sensor_task(void *pvParameter) {
    // VARIABLE DE MEMORIA PARA CUANDO SE SALGA DE LA LÍNEA
    static float ultimo_error_valido = 0.0f; 
    
    while (1) {
        // Lectura cruda de los sensores en ADC1
        int raw_izq = adc1_get_raw(ADC1_CHANNEL_2); // Pin 4
        int raw_cen = adc1_get_raw(ADC1_CHANNEL_3); // Pin 3
        int raw_der = adc1_get_raw(ADC1_CHANNEL_0); // Pin 1

        // Mapeo a escala limpia de 0 a 1000 usando tus promedios
        float val_izq = mapear_sensor(raw_izq);
        float val_cen = mapear_sensor(raw_cen);
        float val_der = mapear_sensor(raw_der);

        float suma_total = val_izq + val_cen + val_der;

        // Si al menos un sensor detecta algo de línea (Suma > 100 en la nueva escala)
        if (suma_total > 100.0f) { 
            shared_error_linea = ((val_izq * -1.0f) + (val_cen * 0.0f) + (val_der * 1.0f)) / suma_total;
            ultimo_error_valido = shared_error_linea; // Guardamos este error en la memoria
            shared_line_detected = true;
        } else {
            // EL ROBOT ESTÁ CIEGO (LOS 3 FUERA DE LA LÍNEA)
            // Usamos la memoria para buscar la línea desesperadamente
            if (ultimo_error_valido > 0.1f) {
                shared_error_linea = 1.0f;  // Se salió por la izquierda, forzar a la derecha al máximo
            } else if (ultimo_error_valido < -0.1f) {
                shared_error_linea = -1.0f; // Se salió por la derecha, forzar a la izquierda al máximo
            } else {
                shared_error_linea = 0.0f;  // Caso raro: se perdió estando perfectamente centrado
            }
            shared_line_detected = false;
        }

        vTaskDelay(pdMS_TO_TICKS(10)); // Lectura rápida de ADC cada 10ms
    }
}

// -------------------------------------------------------------
// TIMER DE NAVEGACIÓN: CALCULA CINEMÁTICA Y PD DE LÍNEA
// -------------------------------------------------------------
static void nav_loop_cb(void *arg) {
    if (!robot_active) return;

    float error_yaw = current_yaw - target_yaw; 
    
    while (error_yaw > 180.0f) error_yaw -= 360.0f;
    while (error_yaw < -180.0f) error_yaw += 360.0f;

    bool time_is_up = esp_timer_get_time() >= movement_end_time;
    bool target_reached = is_pure_turn && (fabs(error_yaw) <= 2.0f);

    if (time_is_up || target_reached) { 
        robot_active = false; 
        is_line_follower = false;
        calculate_kinematics(0.0f, 0.0f, 0.0f);
        ESP_LOGI(TAG, "Meta alcanzada o Tiempo cumplido. Frenando.");
    } else {
        // 1. CÁLCULO DE YAW (Mantiene al robot mirando al frente)
        float current_kp = is_pure_turn ? KP_YAW_TURN : KP_YAW;
        float current_max_wz = is_pure_turn ? MAX_WZ_TURN : MAX_WZ;

        float wz_cmd = error_yaw * current_kp;

        if (wz_cmd > current_max_wz) wz_cmd = current_max_wz;
        if (wz_cmd < -current_max_wz) wz_cmd = -current_max_wz;

        // 2. LÓGICA DEL SEGUIDOR DE LÍNEA (MODO CANGREJO)
        if (is_line_follower) {
            
            float error_linea = shared_error_linea;

            // --- INICIO DE MODIFICACIONES ---
            // BANDA MUERTA: Si el error es muy pequeño, ignóralo para evitar micro-correcciones
            if (fabs(error_linea) < BANDA_MUERTA && shared_line_detected) {
                error_linea = 0.0f; 
            }

            // Controlador PD de Profundidad (Adelante / Atrás)
            // Controlador PD de Profundidad (Adelante / Atrás) INVERTIDO
            float correccion_vy = -((error_linea * KP_LINEA) + ((error_linea - error_linea_ant) * KD_LINEA));
            error_linea_ant = error_linea;

            // LÍMITE DE VELOCIDAD (SATURACIÓN): Para que no dé latigazos
            if (correccion_vy > MAX_CORRECCION_VY) correccion_vy = MAX_CORRECCION_VY;
            if (correccion_vy < -MAX_CORRECCION_VY) correccion_vy = -MAX_CORRECCION_VY;
            // --- FIN DE MODIFICACIONES ---

            // Enviamos Vx (Avance lateral constante), Vy (Corrección de línea), Wz (IMU)
            calculate_kinematics(cmd_vx, correccion_vy, wz_cmd);
        } else {
            // Movimiento manual libre o Giro puro
            calculate_kinematics(cmd_vx, cmd_vy, wz_cmd);
        }
    }
}

// MAIN 
void app_main(void) {
    
    init_motor_gpios();
    init_esp_now(); 

    // CONFIGURACIÓN DE SENSORES ANALÓGICOS TCRT5000 (Resolución 12-bits: 0 a 4095)
    // EXCLUSIVO ADC1 para evitar conflictos con ESP-NOW / Wi-Fi
    adc1_config_width(ADC_WIDTH_BIT_12);
    adc1_config_channel_atten(ADC1_CHANNEL_2, ADC_ATTEN_DB_11); // Pin 4 (Izquierdo)
    adc1_config_channel_atten(ADC1_CHANNEL_3, ADC_ATTEN_DB_11); // Pin 3 (Central)
    adc1_config_channel_atten(ADC1_CHANNEL_0, ADC_ATTEN_DB_11); // Pin 1 (Derecho)

    //CONFIGURACIÓN BUS I2C PARA IMU
    i2c_master_bus_config_t i2c_bus_config = {
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .i2c_port = -1,
        .scl_io_num = I2C_MASTER_SCL_IO,
        .sda_io_num = I2C_MASTER_SDA_IO,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = true,
    };
    i2c_master_bus_handle_t bus_handle;
    ESP_ERROR_CHECK(i2c_new_master_bus(&i2c_bus_config, &bus_handle));

    i2c_device_config_t dev_cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = MPU9250_ADDR,
        .scl_speed_hz = 400000,
    };
    ESP_ERROR_CHECK(i2c_master_bus_add_device(bus_handle, &dev_cfg, &dev_handle));

    mpu9250_init_sensor();
    
    //REPARTE EL TIEMPO DEL PROCESAMIENTO PARA LA LECTURA DE LA IMU Y ADC
    xTaskCreate(imu_heading_task, "imu_heading_task", 4096, NULL, 5, NULL); 
    xTaskCreate(adc_sensor_task, "adc_sensor_task", 4096, NULL, 4, NULL); 

    ledc_timer_config_t ledc_timer = {
        .speed_mode = LEDC_LOW_SPEED_MODE, .duty_resolution = PWM_RESOLUTION,
        .timer_num = LEDC_TIMER_0, .freq_hz = PWM_FREQUENCY, .clk_cfg = LEDC_AUTO_CLK
    };
    ledc_timer_config(&ledc_timer); //CONFIGURACIÓN REGISTROS INTERNOS DEL LEDC PARA GENERAR PWM

    for (int i = 0; i < NUM_MOTORS; i++) {
        ledc_channel_config_t ledc_channel = {
            .speed_mode = LEDC_LOW_SPEED_MODE, .channel = (ledc_channel_t)i, //CONFIGURA VELOCIDAD PWM Y CANAL OFICIAL PARA EL PWM
            .timer_sel = LEDC_TIMER_0, .intr_type = LEDC_INTR_DISABLE, //TIMER 0 PARA LOS 4 MOTORES, INTERRUPCIONES DESACTIVADAS DE PWM
            .gpio_num = motor_pwm_gpio[i], .duty = 0, .hpoint = 0
        };
        ledc_channel_config(&ledc_channel); //CONFIGURA LOS PINES DE PWM PARA CADA MOTOR Y LOS INICIALIZA EN 0 
    }

    mcpwm_cap_timer_handle_t cap_timer0 = NULL, cap_timer1 = NULL; //DOS TIMERS DE CAPTURA PARA LOS 4 ENCODERS 
    mcpwm_capture_timer_config_t t_conf0 = { .group_id = 0 }, t_conf1 = { .group_id = 1 };//CONFIGURACIÓN DE LOS TIMERS DE CAPTURA
    mcpwm_new_capture_timer(&t_conf0, &cap_timer0);
    mcpwm_new_capture_timer(&t_conf1, &cap_timer1);

    for (int i = 0; i < NUM_MOTORS; i++) {
        enc_ctx[i].index = i;
        mcpwm_capture_channel_config_t ch_conf = {
            .gpio_num = encoder_gpio[i], .prescale = 1,
            .flags.pos_edge = true, .flags.pull_up = true //CAPTURA EN FLANCO DE SUBIDA, CON PULL-UP ACTIVADO
        };
        mcpwm_cap_channel_handle_t cap_chan = NULL;//MANEJADOR DE CANAL DE CAPTURA PARA CADA ENCODER
        mcpwm_new_capture_channel((i < 2) ? cap_timer0 : cap_timer1, &ch_conf, &cap_chan);//LOS PRIMEROS 2 MOTORES USAN EL TIMER DE CAPTURA 0, LOS OTROS 2 EL TIMER DE CAPTURA 1
        mcpwm_capture_event_callbacks_t cbs = { .on_cap = encoder_capture_callback };//FUNCIÓN DE CALLBACK PARA FLANCO DE SUBIDA
        mcpwm_capture_channel_register_event_callbacks(cap_chan, &cbs, &enc_ctx[i]);//IDENTIFICACIÓN DEL MOTOR EN EL CALLBACK DE CAPTURA
        mcpwm_capture_channel_enable(cap_chan);//HABILITACIÓN CANAL DE CAPTURA
    }

    mcpwm_capture_timer_enable(cap_timer0);//HABILITACIÓN TIMER DE CAPTURA
    mcpwm_capture_timer_start(cap_timer0);
    
    mcpwm_capture_timer_enable(cap_timer1);
    mcpwm_capture_timer_start(cap_timer1);

    uint64_t start_time = esp_timer_get_time();
    for(int i=0; i<NUM_MOTORS; i++){ last_eval_time[i] = start_time; }

    for (int i = 0; i < NUM_MOTORS; i++) {
        pid_ctrl_parameter_t pid_params = { //PARÁMETROS PID INICIALES PARA CONTROL DE VELOCIDAD DE LOS MOTORES
            .kp = 40.0, .ki = 8.0, .kd = 2.0,
            .cal_type = PID_CAL_TYPE_POSITIONAL, 
            .max_output = PWM_MAX_DUTY, .min_output = 0,
            .max_integral = 1000, .min_integral = -1000,
        };
        pid_ctrl_config_t pid_config = { .init_param = pid_params }; //CONFIGURACIÓN DEL CONTROLADOR PID PARA CADA MOTOR
        pid_new_control_block(&pid_config, &motors[i].pid);
    }

    const esp_timer_create_args_t timer_args = { .callback = pid_loop_cb, .name = "pid_loop" };
    esp_timer_handle_t timer;
    esp_timer_create(&timer_args, &timer);
    esp_timer_start_periodic(timer, PID_LOOP_PERIOD_MS * 1000); 

    // NUEVO TIMER: DIRECTOR DE NAVEGACIÓN (20ms)
    const esp_timer_create_args_t nav_timer_args = { .callback = nav_loop_cb, .name = "nav_loop" };
    esp_timer_handle_t nav_timer;
    esp_timer_create(&nav_timer_args, &nav_timer);
    esp_timer_start_periodic(nav_timer, 20 * 1000); // 20ms exactos
}