#include "robot_config.h"
#include "navigation.h"

static const char *TAG = "NAV";

// DEFINICIÓN DE VARIABLES GLOBALES
volatile float target_speed_rads[NUM_MOTORS] = {0.0f, 0.0f, 0.0f, 0.0f};  
volatile float current_yaw = 0.0f;
volatile float target_yaw = 0.0f;
volatile float cmd_vx = 0.0f;
volatile float cmd_vy = 0.0f;
volatile bool robot_active = false;
uint64_t movement_end_time = 0;
volatile bool is_pure_turn = false;
volatile bool is_line_follower = false;
volatile float shared_error_linea = 0.0f; 
volatile bool shared_line_detected = false; 
// En el código del ROBOT, cambia la MAC a puros FF:
uint8_t pc_mac_address[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
volatile uint8_t line_search_state = 0; 
uint64_t maneuver_wait_end_time = 0; // Temporizador para los 2 segundos
volatile bool is_finding_line_rear = false;
static float error_linea_ant = 0.0f;
volatile bool shared_intersection_detected = false; 
volatile bool vision_tree_centered = false;
volatile bool vision_pool_detected = false;
volatile bool vision_path_clear = false;
static uint64_t intersection_blind_until = 0; // Temporizador de ceguera
volatile bool vision_obstacle = false;
volatile bool is_sequence_play = false;

// --- VARIABLES GLOBALES PARA LA SECUENCIA DE RETORNO ---
volatile uint8_t follower_mode = 0; // 0=Ida, 1=Reversa Izq, 2=Derecha 2s, 3=Vuelta Final
volatile bool final_lap = false;    // Bandera para saber si ya dimos el giro de 180

void calculate_kinematics(float vx, float vy, float wz) {
    float multiplier = -1.0f / WHEEL_RADIUS;
    vx=-vx;
    target_speed_rads[0] = multiplier * (1.0f * vy - 1.0f * vx + ROBOT_L * wz); 
    target_speed_rads[1] = multiplier * (1.0f * vy + 1.0f * vx + ROBOT_L * wz); 
    target_speed_rads[2] = multiplier * (1.0f * vy + 1.0f * vx - ROBOT_L * wz); 
    target_speed_rads[3] = multiplier * (1.0f * vy - 1.0f * vx - ROBOT_L * wz); 
}

static void nav_loop_cb(void *arg) {
    uint64_t now = esp_timer_get_time();

    if (robot_active && now > movement_end_time && line_search_state == 0 && !is_line_follower) {
        robot_active = false;
        ESP_LOGI(TAG, "Tiempo expirado");
    }

    if (!robot_active) {
        calculate_kinematics(0.0f, 0.0f, 0.0f);
        return;
    }

    float error_yaw = current_yaw - target_yaw;

    while (error_yaw > 180.0f) error_yaw -= 360.0f;
    while (error_yaw < -180.0f) error_yaw += 360.0f;

    float wz_cmd = 0.0f;

    if (is_pure_turn) {
        if (fabs(error_yaw) <= 0.5f) {
            ESP_LOGW(TAG, "Giro completado");
            is_pure_turn = false;
            calculate_kinematics(0.0f, 0.0f, 0.0f);

            if (!is_sequence_play) {
                robot_active = false;
            }
            return;
        }
        else {
            float velocidad_giro = fabs(cmd_vx);
            if (velocidad_giro < 0.05f) velocidad_giro = 0.8f;

            if (error_yaw > 0.0f) {
                wz_cmd = velocidad_giro;
            } else {
                wz_cmd = -velocidad_giro;
            }
        }
    }
    else {
        wz_cmd = error_yaw * 0.05f;
        if (wz_cmd > 1.0f) wz_cmd = 1.0f;
        if (wz_cmd < -1.0f) wz_cmd = -1.0f;
    }

    if (is_line_follower && vision_obstacle) { //Detección de grano o contenedor
        vision_obstacle = false;
        is_line_follower = false;

        if (final_lap == true) {
            line_search_state = 100; //Cuando detecta los contenedores de regreo
            maneuver_wait_end_time = now + 500000ULL;
            ESP_LOGW(TAG, "Obstaculo en el regreso Evasion iniciada");
        } else {
            line_search_state = 64;
            ESP_LOGW(TAG, "Obstaculo en la ida Pausa indefinida hasta recibir Letra F");
        }
    }

    // Trampa para la Alberca (Letra P) - ESTA SE QUEDA IGUAL (Es tu paro de emergencia)
    bool permite_vision_P = (line_search_state >= 1 && line_search_state <= 4) ||
                            (line_search_state >= 40 && line_search_state <= 42) ||
                            (line_search_state == 50) || 
                            (line_search_state == 60);

    if (permite_vision_P && vision_pool_detected) {
        vision_pool_detected = false;
        ESP_LOGW(TAG, "Letra P detectada");
        line_search_state = 81;
    }

    // Filtro para F
    if (vision_path_clear) {
        //3 primer desplazamiento en -vx  
        if (line_search_state == 3 || line_search_state == 50 || line_search_state == 64 || line_search_state == 105|| line_search_state == 120) {
            // Es el momento correcto. No hacemos nada.
            // Dejamos que el switch evalúe tu 'case 50' y haga tu rutina original.
        } else {
            // Si la F llega en el arranque (1,2,3) o cuando vas en el ESTADO 60...
            // ¡La destruimos para que el robot la ignore por completo!
            vision_path_clear = false; 
        }
    }

    if (line_search_state > 0) {
        switch (line_search_state) {

            case 81:
                calculate_kinematics(0.0f, 0.0f, 0.0f);
                break;
            //====================Salida del robot===============//
            case 1: //Avanza frontalmente hasta que el sensor trasero detecte la línea negra
                final_lap = false;
                if (ir_rear_val == 1) {
                    line_search_state = 2;
                    maneuver_wait_end_time = now + 2000000ULL;
                    calculate_kinematics(0.0f, 0.0f, 0.0f);
                } else {
                    calculate_kinematics(0.0f, 0.30f, wz_cmd);
                }
                break;
            case 2: // Se detiene dos segundos para estabilizarse y que la Jetson pueda procesar la imagen del frente
                if (now >= maneuver_wait_end_time) {
                    line_search_state = 3;
                } else {
                    calculate_kinematics(0.0f, 0.0f, 0.0f);
                }
                break;
            //==================================================//


            //====================Desplazamiento lateral===============//
            case 3: // Se mueve a la izquierda a -vx hasta detectar la F 
                if (vision_path_clear) {
                    // ¡La Jetson vio el camino libre (F) durante la rutina B!
                    vision_path_clear = false;
                    ESP_LOGW(TAG, "Letra F detectada en Rutina B -> Saltando a Rejilla/Alberca!");
                    line_search_state = 51; // Saltamos al estado de pausa de la alberca
                    maneuver_wait_end_time = now + 2000000ULL; // Pausa de 2s
                    calculate_kinematics(0.0f, 0.0f, 0.0f);
                } 
                else if (ir_left_val == 1) {
                    // Si no llega la F y toca la línea, sigue su secuencia normal hacia los árboles
                    line_search_state = 35; // Freno activo
                    maneuver_wait_end_time = now + 1000000ULL;
                    calculate_kinematics(0.06f, 0.0f, 0.0f); // Contramarcha a la derecha
                } 
                else {
                    // Movimiento lateral continuo
                    calculate_kinematics(-0.15f, 0.0f, wz_cmd);
                }
                break;
            //======================================================//
            case 35: // NUEVO: Freno activo de búsqueda
                if (now >= maneuver_wait_end_time) {
                    line_search_state = 4;
                    maneuver_wait_end_time = now + 500000ULL; // Freno seco estabilizador
                    calculate_kinematics(0.0f, 0.0f, 0.0f);
                } else {
                    calculate_kinematics(0.06f, 0.0f, 0.0f);
                }
                break;
            case 4:
                if (now >= maneuver_wait_end_time) {
                    if (is_sequence_play) {
                        line_search_state = 40;
                    } else {
                        line_search_state = 0;
                        robot_active = false;
                    }
                } else {
                    calculate_kinematics(0.0f, 0.0f, 0.0f);
                }
                break;

            case 20:
                if (now >= maneuver_wait_end_time) {
                    line_search_state = 21;
                    maneuver_wait_end_time = now + 3000000ULL;
                } else {
                    calculate_kinematics(-0.15f, 0.0f, wz_cmd);
                }
                break;
            case 21:
                if (now >= maneuver_wait_end_time) {
                    line_search_state = 22;
                } else {
                    calculate_kinematics(0.0f, 0.30f, wz_cmd);
                }
                break;
            case 22:
                if (shared_line_detected) {
                    line_search_state = 0;
                    robot_active = false;
                    calculate_kinematics(0.0f, 0.0f, 0.0f);
                } else {
                    calculate_kinematics(-0.15f, 0.0f, wz_cmd);
                }
                break;

            case 40:
                if (vision_tree_centered) {
                    vision_tree_centered = false;
                    line_search_state = 41;
                    maneuver_wait_end_time = now + 3000000ULL;
                    calculate_kinematics(0.0f, 0.0f, 0.0f);
                }
                else if (ir_right_val == 1) {
                    line_search_state = 42;
                    maneuver_wait_end_time = now + 500000ULL;
                    calculate_kinematics(0.0f, 0.0f, 0.0f);
                }
                else {
                    calculate_kinematics(0.15f, 0.0f, wz_cmd);
                }
                break;
            case 41:
                if (now >= maneuver_wait_end_time) {
                    line_search_state = 40;
                } else {
                    calculate_kinematics(0.0f, 0.0f, 0.0f);
                }
                break;
            case 42:
                if (now >= maneuver_wait_end_time) {
                    if (is_sequence_play) {
                        line_search_state = 50;
                    } else {
                        line_search_state = 0;
                        robot_active = false;
                    }
                } else {
                    calculate_kinematics(0.0f, 0.0f, 0.0f);
                }
                break;

            case 50:
                if (vision_path_clear) {
                    vision_path_clear = false;
                    line_search_state = 51;
                    maneuver_wait_end_time = now + 2000000ULL;
                    calculate_kinematics(0.0f, 0.0f, 0.0f);
                } else {
                    calculate_kinematics(-0.15f, 0.0f, wz_cmd);
                }
                break;

            //==================Rutina evasión de albercas=================//
            case 51:
                if (now >= maneuver_wait_end_time) {
                    line_search_state = 52;
                    maneuver_wait_end_time = now + 3500000ULL; //Freno para estabilizarse
                } else {
                    calculate_kinematics(0.0f, 0.0f, 0.0f);
                }
                break;
            case 52: //Avanza frontalmente para rodear la alberca durante 3.5 segundos
                if (now >= maneuver_wait_end_time) {
                    if (is_sequence_play) {
                        line_search_state = 60;
                    } else {
                        line_search_state = 0;
                        robot_active = false;
                    }
                    calculate_kinematics(0.0f, 0.0f, 0.0f);
                } else {
                    calculate_kinematics(0.0f, 0.30f, wz_cmd);
                }
                break;

            case 60: // Se mueve a la izquierda a -vx hasta detectar la línea negra con el sensor izquierdo
                if (ir_left_val == 1) {
                    line_search_state = 65; // Freno activo
                    maneuver_wait_end_time = now + 500000ULL;
                    calculate_kinematics(0.06f, 0.0f, 0.0f); // Contramarcha a la derecha
                } else {
                    calculate_kinematics(-0.15f, 0.0f, wz_cmd);
                }
                break;
            
            //===============================================================//


            //==================Rutina acomodo sobre la línea=================//
            case 65: // Se desplaza a la derecha para que la rueda no toque la línea
                if (now >= maneuver_wait_end_time) {
                    line_search_state = 61;
                    maneuver_wait_end_time = now + 500000ULL;
                    calculate_kinematics(0.0f, 0.0f, 0.0f);
                } else {
                    calculate_kinematics(0.06f, 0.0f, 0.0f);
                }
                break;
            case 61: //Se detiene para estabilizarse 
                if (now >= maneuver_wait_end_time) {
                    line_search_state = 62;
                    maneuver_wait_end_time = now + 500000ULL;
                } else {
                    calculate_kinematics(0.0f, 0.0f, 0.0f);
                }
                break;
            case 62://Avanza frontalmente hasta que el sensor frontal detecte la línea negra
                if (now >= maneuver_wait_end_time && start_line_left_analog) {
                    line_search_state = 63;
                    maneuver_wait_end_time = now + 1000000ULL;
                    calculate_kinematics(0.0f, 0.0f, 0.0f);
                } else {
                    calculate_kinematics(0.0f, 0.15f, wz_cmd);
                }
                break;

            case 63:// Se detiene para estabilizarse y luego activa el seguidor de línea
                if (now >= maneuver_wait_end_time) {
                    line_search_state = 0;
                    is_line_follower = true;
                    cmd_vx = 0.15f;
                    follower_mode = 0;
                    movement_end_time = now + 15000000ULL;
                } else {
                    calculate_kinematics(0.0f, 0.0f, 0.0f);
                } 
                break;
            
            //===============================================================//


            //========================Rutina para O detectada============================//
            case 64:
                if (vision_path_clear) { // Si la Jetson detectó que el camino está libre, continúa el seguidor 
                    vision_path_clear = false;
                    line_search_state = 0;
                    is_line_follower = true;
                } else {
                    calculate_kinematics(0.0f, 0.0f, 0.0f);
                }
                break;
            //==========================================================================//

            
            
            //=======================Rutina recolección segundo nivel========================//
            case 89: //Cuando se detecta la línea negra sensor derecho aplica la contramarcha
                if (now >= maneuver_wait_end_time) {
                    line_search_state = 90; 
                    maneuver_wait_end_time = now + 2000000ULL;
                    calculate_kinematics(0.0f, 0.0f, 0.0f);
                } else {
                    calculate_kinematics(-0.06f, 0.0f, 0.0f);
                }
                break;
            
            

            case 90: //Activa el seguidor de línea con -vx
                if (now >= maneuver_wait_end_time) {
                    line_search_state = 0;
                    is_line_follower = true;
                    follower_mode = 1;
                    cmd_vx = -0.15f;
                } else {
                    calculate_kinematics(0.0f, 0.0f, 0.0f);
                }
                break;
    
            //=========================================================================//


            case 91: 
                if (now >= maneuver_wait_end_time) {
                    line_search_state = 92; 
                    maneuver_wait_end_time = now + 2000000ULL; 
                    target_yaw = 0.0f; 
                } else {
                    calculate_kinematics(0.06f, 0.0f, 0.0f);
                }
                break;


            //=================================Rutina de regreso===============================//
            case 92: // Desplazamiento lateral para el giro de 180°
                if (now >= maneuver_wait_end_time) {
                    line_search_state = 93; 
                    maneuver_wait_end_time = now + 150000ULL; 
                } else {
                    calculate_kinematics(0.15f, 0.0f, wz_cmd); 
                }
                break;

            case 93: 
                if (now >= maneuver_wait_end_time) {
                    line_search_state = 94; // Pasa a preparar el giro de 180
                    maneuver_wait_end_time = now + 500000ULL; 
                    calculate_kinematics(0.0f, 0.0f, 0.0f);
                } else {
                    calculate_kinematics(0.15f, 0.0f, 0.0f); 
                }
                break;
            //===========================================================================//
            
            //=======================Rutina de giro de 180° para regreso========================//
            case 94:
                if (now >= maneuver_wait_end_time) { //Gira 90° 
                    float offset = -90.0f;
                    float nuevo_target = current_yaw + offset;
                    while (nuevo_target > 180.0f) nuevo_target -= 360.0f;
                    while (nuevo_target < -180.0f) nuevo_target += 360.0f;
                    target_yaw = nuevo_target;
                    is_pure_turn = true;
                    cmd_vx = 0.1f;
                    line_search_state = 95;
                } else {
                    calculate_kinematics(0.0f, 0.0f, 0.0f);
                }
                break;

            case 95: //Hace una pausa de un segundo
                if (!is_pure_turn) {
                    line_search_state = 96;
                    maneuver_wait_end_time = now + 1000000ULL;
                } else {
                    calculate_kinematics(0.0f, 0.0f, wz_cmd);
                }
                break;

            case 96://Gira otros 90° para completar los 180°
                if (now >= maneuver_wait_end_time) {
                    float offset = -90.0f;
                    float nuevo_target = current_yaw + offset;
                    while (nuevo_target > 180.0f) nuevo_target -= 360.0f;
                    while (nuevo_target < -180.0f) nuevo_target += 360.0f;
                    target_yaw = nuevo_target;
                    is_pure_turn = true;
                    cmd_vx = 0.1f;
                    line_search_state = 97;
                } else {
                    calculate_kinematics(0.0f, 0.0f, 0.0f);
                }
                break;

            case 97: //Cuando ya teminó de girar, activa la bander de regreso final
                if (!is_pure_turn) {
                    final_lap = true;
                    line_search_state = 120;
                } else {
                    calculate_kinematics(0.0f, 0.0f, wz_cmd);
                }
                break;
            //=================================================================================//
            
            // ================= RUTINA EVASIÓN DE REJILLA (REGRESO) =================
            
            case 120: // Se desplaza a la izquierda (-vx) buscando el hueco (F)
                if (vision_path_clear) {
                    vision_path_clear = false; 
                    line_search_state = 121;
                    maneuver_wait_end_time = now + 2000000ULL; // Freno de 2s para estabilizar (como tu case 51)
                    calculate_kinematics(0.0f, 0.0f, 0.0f);
                } else {
                    calculate_kinematics(-0.15f, 0.0f, wz_cmd); // Moviéndose a la izquierda
                }
                break;

            case 121: // Pausa de estabilización
                if (now >= maneuver_wait_end_time) {
                    line_search_state = 122;
                    maneuver_wait_end_time = now + 3500000ULL; // 3.5s para cruzar de frente 
                } else {
                    calculate_kinematics(0.0f, 0.0f, 0.0f);
                }
                break;

            case 122: // Avanza frontalmente para rodear la alberca
                if (now >= maneuver_wait_end_time) {
                    line_search_state = 123; // Ya cruzó, ahora a buscar la línea
                } else {
                    calculate_kinematics(0.0f, 0.30f, wz_cmd);
                }
                break;

            case 123: // Continúa desplazándose en -vx hasta que el sensor izquierdo detecte la línea (como tu case 60)
                if (ir_left_val == 1) { 
                    line_search_state = 124; // Pasa al freno activo
                    maneuver_wait_end_time = now + 1000000ULL; // 1 segundo de freno
                    calculate_kinematics(0.06f, 0.0f, 0.0f); // Contramarcha a la derecha para frenar
                } else {
                    calculate_kinematics(-0.15f, 0.0f, wz_cmd); // Sigue a la izquierda
                }
                break;
            
            // ================= RUTINA seguidor de línea depósito granos =================

            case 124: // Espera a que termine el freno activo lateral
                if (now >= maneuver_wait_end_time) {
                    line_search_state = 125; 
                } else {
                    calculate_kinematics(0.06f, 0.0f, 0.0f); // Mantiene contramarcha
                }
                break;

            case 125: 
                if (shared_line_detected) { 
                    line_search_state = 126; // Pasa a la pausa de estabilización final
                    maneuver_wait_end_time = now + 1000000ULL; // 1 segundo de pausa
                    calculate_kinematics(0.0f, 0.0f, 0.0f); // Frenos en seco
                } else {
                    // Avanza suavemente hacia el frente (Vy = 0.15f)
                    calculate_kinematics(0.0f, 0.15f, wz_cmd); 
                }
                break;

            case 126: // Espera a estabilizarse e inicia el Seguidor de Línea FINAL
                if (now >= maneuver_wait_end_time) {
                    line_search_state = 0;
                    is_line_follower = true; // ¡Piloto automático activado!
                    
                    follower_mode = 3;       // ¡MANTENEMOS EL MODO 3 PARA LA META!
                    
                    cmd_vx = 0.15f; 
                    movement_end_time = now + 15000000ULL;
                } else {
                    calculate_kinematics(0.0f, 0.0f, 0.0f); // Mantiene el robot quieto
                }
                break;
            // =================================================================================================//
            
            
        

            //===========================Rutina reversa depósito de granos=============================//
            case 100:
                if (now >= maneuver_wait_end_time) { //Primer giro de 90°
                    float offset = -90.0f;
                    float nuevo_target = current_yaw + offset;
                    while (nuevo_target > 180.0f) nuevo_target -= 360.0f;
                    while (nuevo_target < -180.0f) nuevo_target += 360.0f;
                    target_yaw = nuevo_target;
                    is_pure_turn = true;
                    cmd_vx = 0.1f;
                    line_search_state = 101;
                } else {
                    calculate_kinematics(0.0f, 0.0f, 0.0f);
                }
                break;

            case 101:
                if (!is_pure_turn) {
                    line_search_state = 102;
                    maneuver_wait_end_time = now + 1000000ULL;
                } else {
                    calculate_kinematics(0.0f, 0.0f, wz_cmd);
                }
                break;

            case 102://Sregundo giro de 90° para quedar en reversa
                if (now >= maneuver_wait_end_time) {
                    float offset = -90.0f;
                    float nuevo_target = current_yaw + offset;
                    while (nuevo_target > 180.0f) nuevo_target -= 360.0f;
                    while (nuevo_target < -180.0f) nuevo_target += 360.0f;
                    target_yaw = nuevo_target;
                    is_pure_turn = true;
                    cmd_vx = 0.1f;
                    line_search_state = 103;
                } else {
                    calculate_kinematics(0.0f, 0.0f, 0.0f);
                }
                break;

            case 103:
                if (!is_pure_turn) {
                    line_search_state = 104;
                    maneuver_wait_end_time = now + 500000ULL;
                } else {
                    calculate_kinematics(0.0f, 0.0f, wz_cmd);
                }
                break;
            
            
            case 104: // Reversa para quedar a la altura del contenedor 
                if (now >= maneuver_wait_end_time) {
                    line_search_state = 105;
                } else {
                    calculate_kinematics(0.0f, -0.15f, 0.0f);
                }
                break;
            //==================================================================================//
            
            //===========================Rutina incorporación seguidor=============================//
            case 105:
                if (vision_path_clear) {
                    vision_path_clear = false;
                    line_search_state = 106;
                    maneuver_wait_end_time = now + 500000ULL;
                } else {
                    calculate_kinematics(0.0f, 0.0f, 0.0f);
                }
                break;

            case 106:
                if (now >= maneuver_wait_end_time) { //Avanza frontal para reincorporarse a la línea
                    line_search_state = 107;
                    maneuver_wait_end_time = now + 500000ULL;
                } else {
                    calculate_kinematics(0.0f, 0.15f, 0.0f);
                }
                break;

            case 107: //Primer giro de 90°
                if (now >= maneuver_wait_end_time) {
                    float offset = -90.0f;
                    float nuevo_target = current_yaw + offset;
                    while (nuevo_target > 180.0f) nuevo_target -= 360.0f;
                    while (nuevo_target < -180.0f) nuevo_target += 360.0f;
                    target_yaw = nuevo_target;
                    is_pure_turn = true;
                    cmd_vx = 0.1f;
                    line_search_state = 108;
                } else {
                    calculate_kinematics(0.0f, 0.0f, 0.0f);
                }
                break;

            case 108:
                if (!is_pure_turn) {
                    line_search_state = 109;
                    maneuver_wait_end_time = now + 1000000ULL;
                } else {
                    calculate_kinematics(0.0f, 0.0f, wz_cmd);
                }
                break;

            case 109: //Segundo giro de 90° 
                if (now >= maneuver_wait_end_time) {
                    float offset = -90.0f;
                    float nuevo_target = current_yaw + offset;
                    while (nuevo_target > 180.0f) nuevo_target -= 360.0f;
                    while (nuevo_target < -180.0f) nuevo_target += 360.0f;
                    target_yaw = nuevo_target;
                    is_pure_turn = true;
                    cmd_vx = 0.1f;
                    line_search_state = 110;
                } else {
                    calculate_kinematics(0.0f, 0.0f, 0.0f);
                }
                break;

            case 110: //Continúa el seguidor de línea despúes de depositar 
                if (!is_pure_turn) {
                    line_search_state = 0;
                    is_line_follower = true;
                } else {
                    calculate_kinematics(0.0f, 0.0f, wz_cmd);
                }
                break;
            //==================================================================================//
            
            case 111: // Freno para contramarcha 
                if (now >= maneuver_wait_end_time) {
                    line_search_state = 0; // Termina la secuencia
                    robot_active = false;
                    calculate_kinematics(0.0f, 0.0f, 0.0f);
                } else {
                    calculate_kinematics(-0.06f, 0.0f, 0.0f);
                }
                break;
        }
    } else if (is_line_follower) { 
        if (follower_mode == 0 && ir_right_val == 1) { //Si el sensor derecho detecta la línea negra y está de ida 
            is_line_follower = false;
            line_search_state = 89;
            maneuver_wait_end_time = now + 1000000ULL;
            calculate_kinematics(0.0f, 0.0f, 0.0f);
            return;
        } else if (follower_mode == 1 && ir_left_val == 1) { //Si el sensor izquierdo detecta la línea negra y está de vuelta segundo nivel arbol
            is_line_follower = false;
            line_search_state = 92;
            maneuver_wait_end_time = now + 1000000ULL;
            calculate_kinematics(0.0f, 0.0f, 0.0f);
            return;
        } else if (follower_mode == 3 && ir_right_val == 1) { //Cuando termina el recorrido 
            is_line_follower = false;
            robot_active = false;
            calculate_kinematics(0.0f, 0.0f, 0.0f);
            return;
        }

        float correccion_vy = 0.0f;

        if (shared_intersection_detected) { //Si está en una intersección activa un temporizador 
            intersection_blind_until = now + 2000000ULL;
        }

        if (shared_intersection_detected || now < intersection_blind_until) { //Si los tres están en negro se guía por la IMU durante 2s
            correccion_vy = 0.0f;
            error_linea_ant = 0.0f;
        } else { //Controlador PID para el seguidor de línea 
            float error_linea = shared_error_linea;
            if (fabs(error_linea) < BANDA_MUERTA && shared_line_detected) {
                error_linea = 0.0f;
            }
            correccion_vy = -((error_linea * KP_LINEA) + ((error_linea - error_linea_ant) * KD_LINEA));
            error_linea_ant = error_linea;
        }

        if (correccion_vy > MAX_CORRECCION_VY) correccion_vy = MAX_CORRECCION_VY;
        if (correccion_vy < -MAX_CORRECCION_VY) correccion_vy = -MAX_CORRECCION_VY;

        calculate_kinematics(cmd_vx, correccion_vy, wz_cmd); 
    } else {
        if (is_pure_turn) {
            calculate_kinematics(0.0f, 0.0f, wz_cmd);
        } else {
            calculate_kinematics(cmd_vx, cmd_vy, wz_cmd);
        }
    }
}

void init_navigation(void) {
    const esp_timer_create_args_t nav_timer_args = { .callback = nav_loop_cb, .name = "nav_loop" };
    esp_timer_handle_t nav_timer;
    esp_timer_create(&nav_timer_args, &nav_timer);
    esp_timer_start_periodic(nav_timer, 20 * 1000); // 20ms
}