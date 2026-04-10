#ifndef ROBOT_CONFIG_H
#define ROBOT_CONFIG_H

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
#include "driver/adc.h"
#include "esp_wifi.h"
#include "esp_now.h"
#include "esp_netif.h"
#include "esp_mac.h"
#include "nvs_flash.h"

// ==========================================
// CONSTANTES Y DEFINICIONES GLOBALES
// ==========================================
#define NUM_MOTORS          4
#define ENCODER_CPR         764.3f
#define PID_LOOP_PERIOD_MS  50    
#define WHEEL_RADIUS        0.04f  
#define ROBOT_L             0.64f  

#define KP_YAW              0.08f  
#define MAX_WZ              3.0f   
#define KP_YAW_TURN         0.015f 
#define MAX_WZ_TURN         0.5f   

#define KP_LINEA            0.06f  
#define KD_LINEA            0.55f  
#define MAX_CORRECCION_VY   0.10f  

#define BANDA_MUERTA        0.15f 
#define VALOR_BLANCO        350.0f
#define VALOR_NEGRO         4000.0f
#define I2C_MASTER_SDA_IO   15   
#define I2C_MASTER_SCL_IO   16
#define MPU9250_ADDR        0x68
#define PWR_MGMT_1          0x6B
#define GYRO_CONFIG         0x1B
#define GYRO_ZOUT_H         0x47

#define PWM_FREQUENCY       20000
#define PWM_RESOLUTION      LEDC_TIMER_10_BIT
#define PWM_MAX_DUTY        1023

#define PIN_IR_LEFT         48
#define PIN_IR_RIGHT        14
#define PIN_IR_REAR         10

// ==========================================
// ESTRUCTURAS
// ==========================================
typedef struct __attribute__((packed)) { 
    char cmd;        
    uint8_t padding[3];  // <--- AGREGAMOS 3 BYTES DE RELLENO
    float vx;
    float vy;
    float target_yaw;
    int duration_ms; 
} control_cmd_t;

typedef struct __attribute__((packed)) {
    uint16_t header;
    char jetson_cmd;
    float yaw;
    float omega[4];  
} telemetry_data_t;

// ==========================================
// VARIABLES GLOBALES (EXTERN)
// ==========================================
extern volatile float target_speed_rads[NUM_MOTORS];
extern volatile float current_yaw;
extern volatile float target_yaw;
extern volatile float cmd_vx;
extern volatile float cmd_vy;
extern volatile bool robot_active;
extern uint64_t movement_end_time;
extern uint64_t maneuver_wait_end_time; // <--- ¡AGREGA ESTA LÍNEA!
extern volatile bool is_pure_turn;
extern volatile bool is_line_follower;
extern volatile float shared_error_linea;
extern volatile bool shared_line_detected;
extern uint8_t pc_mac_address[6];
extern volatile int ir_left_val;
extern volatile int ir_right_val;
extern volatile int ir_rear_val;
// Variable para la máquina de estados de búsqueda
extern volatile uint8_t line_search_state;
extern volatile bool shared_intersection_detected; // <--- NUEVA BANDERA
// Banderas simuladas de la Jetson Orin
extern volatile bool vision_tree_centered; // Se activa cuando centras un árbol
extern volatile bool vision_pool_detected; // Se activa cuando hay una alberca en frente
extern volatile bool vision_path_clear;    // Se activa cuando el espacio de enfrente está libre
extern volatile bool vision_obstacle; // <--- NUEVA BANDERA
extern volatile bool is_sequence_play; // <--- NUEVA BANDERA
extern volatile bool start_line_left_analog;
extern volatile char current_jetson_cmd; // Guarda la última letra de la Jetson
#endif