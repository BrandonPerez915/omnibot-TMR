#include "robot_config.h"
#include "navigation.h"
#include "driver/spi_slave.h"
#include "driver/gpio.h"
#include <string.h>
#include "esp_wifi.h"
#include "esp_now.h"
#include "esp_netif.h"
#include "nvs_flash.h"

static const char *TAG = "COMMS";

#define PIN_NUM_MOSI 35
#define PIN_NUM_MISO 36
#define PIN_NUM_CLK  37
#define PIN_NUM_CS   39

extern uint8_t pc_mac_address[6];
volatile char current_jetson_cmd = '-'; // <--- NACE LA VARIABLE AQUÍ

// ================= INICIALIZACIÓN DE ESP-NOW (RADIO) =================
void init_esp_now_robot() {
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_start());
    ESP_ERROR_CHECK(esp_now_init());

    esp_now_peer_info_t peerInfo = {};
    memcpy(peerInfo.peer_addr, pc_mac_address, 6);
    peerInfo.channel = 1;  
    peerInfo.encrypt = false;
    esp_now_add_peer(&peerInfo);
}

// ================= TAREA DE COMUNICACIÓN SPI =================
void spi_slave_task(void *pvParameters) {
    WORD_ALIGNED_ATTR uint8_t recvbuf[4];
    WORD_ALIGNED_ATTR uint8_t sendbuf[4]; 
    memset(recvbuf, 0, sizeof(recvbuf));
    memset(sendbuf, 0, sizeof(sendbuf));

    spi_slave_transaction_t t;
    memset(&t, 0, sizeof(t));

    while (1) {
        t.length = 32; 
        t.tx_buffer = sendbuf;
        t.rx_buffer = recvbuf;

        // Aquí el robot se bloquea esperando a la Jetson (¡Pero ya no afecta a la telemetría!)
        esp_err_t ret = spi_slave_transmit(SPI2_HOST, &t, portMAX_DELAY);
        
        if (ret == ESP_OK) {
            char cmd_char = recvbuf[0]; 
            current_jetson_cmd = cmd_char; // Actualizamos la letra para que motors.c la lea

            ESP_LOGW(TAG, ">>> SPI RECIBIDO <<< Letra cruda: [%c]", cmd_char);

            // ==========================================================
            // LÓGICA DE NAVEGACIÓN
            // ==========================================================
            if (cmd_char == 'K' || cmd_char == 'k') {
                ESP_LOGI(TAG, "CMD Recibido: Avance basico manual");
                cmd_vx = 0.15f; cmd_vy = 0.0f; target_yaw = current_yaw;
                is_pure_turn = false; is_line_follower = false; is_sequence_play = false;
                movement_end_time = esp_timer_get_time() + 5000000ULL; 
                robot_active = true;
                
            } else if (cmd_char == 'E' || cmd_char == 'e') {
                ESP_LOGW(TAG, "INICIANDO SECUENCIA MAESTRA!");
                is_sequence_play = true; line_search_state = 1;        
                is_pure_turn = false; is_line_follower = false;
                target_yaw = current_yaw; 
                movement_end_time = esp_timer_get_time() + 300000000ULL; 
                robot_active = true;

            } else if (cmd_char == 'G' || cmd_char == 'g') {
                ESP_LOGI(TAG, "CMD Giro Relativo");
                cmd_vx = 0.0f; cmd_vy = 0.0f;
                float nuevo_target = current_yaw + 90.0f; 
                while (nuevo_target > 180.0f) nuevo_target -= 360.0f;
                while (nuevo_target < -180.0f) nuevo_target += 360.0f;
                target_yaw = nuevo_target;
                is_pure_turn = true; is_line_follower = false; is_sequence_play = false;
                movement_end_time = esp_timer_get_time() + 10000000ULL; 
                robot_active = true;
                
            } else if (cmd_char == 'L' || cmd_char == 'l') { 
                ESP_LOGI(TAG, "CMD Seguidor de Linea Libre");
                cmd_vx = 0.15f; cmd_vy = 0.0f; target_yaw = current_yaw; 
                is_pure_turn = false; is_line_follower = true; is_sequence_play = false;
                movement_end_time = esp_timer_get_time() + 300000000ULL;
                robot_active = true;
                
            } else if (cmd_char == 'S' || cmd_char == 's') {
                robot_active = false; is_line_follower = false; is_sequence_play = false;
                calculate_kinematics(0.0f, 0.0f, 0.0f);
                
            } else if (cmd_char == 'B' || cmd_char == 'b') {
                line_search_state = 1; is_pure_turn = false; is_line_follower = false; is_sequence_play = false;
                target_yaw = current_yaw; movement_end_time = esp_timer_get_time() + 60000000ULL;
                robot_active = true;
                
            } else if (cmd_char == 'M' || cmd_char == 'm') {
                line_search_state = 20; is_pure_turn = false; is_line_follower = false; is_sequence_play = false;
                target_yaw = current_yaw; maneuver_wait_end_time = esp_timer_get_time() + 5000000ULL; 
                movement_end_time = esp_timer_get_time() + 60000000ULL; robot_active = true;
                
            } else if (cmd_char == 'C' || cmd_char == 'c') {
                line_search_state = 60; is_pure_turn = false; is_line_follower = false; is_sequence_play = false;
                target_yaw = current_yaw; movement_end_time = esp_timer_get_time() + 60000000ULL; robot_active = true;

            } else if (cmd_char == 'R' || cmd_char == 'r') {
                line_search_state = 40; is_pure_turn = false; is_line_follower = false; is_sequence_play = false;
                target_yaw = current_yaw; movement_end_time = esp_timer_get_time() + 60000000ULL; robot_active = true;

            } else if (cmd_char == 'A' || cmd_char == 'a') {
                line_search_state = 50; is_pure_turn = false; is_line_follower = false; is_sequence_play = false;
                target_yaw = current_yaw; movement_end_time = esp_timer_get_time() + 60000000ULL; robot_active = true;

            } else if (cmd_char == 'T' || cmd_char == 't') {
                vision_tree_centered = true;
            } else if (cmd_char == 'P' || cmd_char == 'p') {
                vision_pool_detected = true;
            } else if (cmd_char == 'F' || cmd_char == 'f') { 
                vision_path_clear = true;
            } else if (cmd_char == 'O' || cmd_char == 'o') { 
                vision_obstacle = true;
            }
        }
    }
}

void init_comms(void) {
    init_esp_now_robot();

    spi_bus_config_t buscfg = {
        .mosi_io_num = PIN_NUM_MOSI, .miso_io_num = PIN_NUM_MISO,
        .sclk_io_num = PIN_NUM_CLK, .quadwp_io_num = -1, .quadhd_io_num = -1,
    };
    spi_slave_interface_config_t slvcfg = {
        .mode = 0, .spics_io_num = PIN_NUM_CS, .queue_size = 3, .flags = 0,
    };

    gpio_set_pull_mode(PIN_NUM_MOSI, GPIO_PULLUP_ONLY);
    gpio_set_pull_mode(PIN_NUM_CLK, GPIO_PULLUP_ONLY);
    gpio_set_pull_mode(PIN_NUM_CS, GPIO_PULLUP_ONLY);

    ESP_ERROR_CHECK(spi_slave_initialize(SPI2_HOST, &buscfg, &slvcfg, SPI_DMA_CH_AUTO));
    xTaskCreate(spi_slave_task, "spi_slave_task", 4096, NULL, 5, NULL);
    ESP_LOGI(TAG, "Comunicaciones SPI Slave y ESP-NOW inicializadas");
}