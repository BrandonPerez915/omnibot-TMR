#include "robot_config.h"
#include "sensors.h"

volatile int ir_left_val = 1;
volatile int ir_right_val = 1;
volatile int ir_rear_val = 1;
volatile bool start_line_left_analog = false;

static const char *TAG = "SENSORS";
i2c_master_dev_handle_t dev_handle;

float mapear_sensor(int raw_val) {
    float val = (float)raw_val;
    if (val < VALOR_BLANCO) val = VALOR_BLANCO;
    if (val > VALOR_NEGRO) val = VALOR_NEGRO;
    return ((val - VALOR_BLANCO) * 1000.0f) / (VALOR_NEGRO - VALOR_BLANCO);
}

float read_gyro_z() {
    uint8_t reg = GYRO_ZOUT_H;
    uint8_t data[2] = {0, 0};
    esp_err_t ret = i2c_master_transmit_receive(dev_handle, &reg, 1, data, 2, -1);
    if (ret != ESP_OK) return 0.0;
    int16_t raw_z = (int16_t)((data[0] << 8) | data[1]);
    return (float)raw_z / 131.0; 
}

void mpu9250_init_sensor() {
    uint8_t data[2];
    data[0] = PWR_MGMT_1; data[1] = 0x80; 
    i2c_master_transmit(dev_handle, data, 2, -1); 
    vTaskDelay(pdMS_TO_TICKS(100));
    data[0] = PWR_MGMT_1; data[1] = 0x03; 
    i2c_master_transmit(dev_handle, data, 2, -1);
    data[0] = GYRO_CONFIG; data[1] = 0x00; 
    i2c_master_transmit(dev_handle, data, 2, -1);
    ESP_LOGI(TAG, "MPU9250 inicializado");
}

void imu_heading_task(void *pvParameter) {
    float yaw = 0;
    float dt = 0.02; 
    float gyro_bias_z = 0;
    float filtered_gz = 0;
    const float alpha = 0.15f; 

    ESP_LOGI(TAG, "ESTABILIZANDO IMU");
    for(int i = 0; i < 100; i++) { read_gyro_z(); vTaskDelay(pdMS_TO_TICKS(5)); }
    ESP_LOGI(TAG, "CALIBRANDO IMU");
    for(int i = 0; i < 1000; i++) { gyro_bias_z += read_gyro_z(); vTaskDelay(pdMS_TO_TICKS(5)); }
    gyro_bias_z /= 1000.0;

    while (1) {
        float raw_gz = read_gyro_z() - gyro_bias_z;
        filtered_gz = (alpha * raw_gz) + ((1.0f - alpha) * filtered_gz);
        if (fabs(filtered_gz) > 0.25f) yaw += filtered_gz * dt;
        
        if (yaw > 180.0f) yaw -= 360.0f;
        if (yaw < -180.0f) yaw += 360.0f;
        current_yaw = yaw;
        vTaskDelay(pdMS_TO_TICKS(20));
    }
}

void adc_sensor_task(void *pvParameter) {
    static float ultimo_error_valido = 0.0f; 
    int debug_counter = 0; 

    while (1) {
        ir_left_val = gpio_get_level(PIN_IR_LEFT);
        ir_right_val = gpio_get_level(PIN_IR_RIGHT);
        ir_rear_val = gpio_get_level(PIN_IR_REAR);

        int raw_izq = adc1_get_raw(ADC1_CHANNEL_2);
        int raw_cen = adc1_get_raw(ADC1_CHANNEL_3);
        int raw_der = adc1_get_raw(ADC1_CHANNEL_0);

        float val_izq = mapear_sensor(raw_izq);
        float val_cen = mapear_sensor(raw_cen);
        float val_der = mapear_sensor(raw_der);  
        
        start_line_left_analog = (raw_izq > 500.0f || raw_cen > 500.0f || raw_der > 500.0f); // <--- NUEVA REGLA PARA INICIAR BÚSQUEDA

        debug_counter++;
        if (debug_counter >= 50) { 
          ESP_LOGI(TAG, "ANALOG Frente -> IZQ: %d | CEN: %d | DER: %d", raw_izq, raw_cen, raw_der);
            ESP_LOGW(TAG, "DIGITAL Frenos-> IZQ: %d | DER: %d | TRASERO: %d", ir_left_val, ir_right_val, ir_rear_val);
           ESP_LOGI(TAG, "IMU Orientacion-> Yaw Actual: %.2f grados", current_yaw);
            debug_counter = 0;
        }

        float suma_total = val_izq + val_cen + val_der;

        if (val_izq > 600.0f && val_der > 600.0f) {
            shared_intersection_detected = true;
            shared_error_linea = 0.0f; 
            shared_line_detected = true;
        } 
        else if (suma_total > 100.0f) {
            shared_intersection_detected = false;
            shared_error_linea = ((val_izq * -1.0f) + (val_cen * 0.0f) + (val_der * 1.0f)) / suma_total;
            ultimo_error_valido = shared_error_linea; 
            shared_line_detected = true;
        } 
        else {
            shared_intersection_detected = false;
            if (ultimo_error_valido > 0.1f) shared_error_linea = 1.0f;  
            else if (ultimo_error_valido < -0.1f) shared_error_linea = -1.0f; 
            else shared_error_linea = 0.0f;  
            shared_line_detected = false;
        }
        
        vTaskDelay(pdMS_TO_TICKS(10)); 
    }
}

void init_sensors(void) {
    gpio_set_direction(PIN_IR_LEFT, GPIO_MODE_INPUT);
    gpio_set_direction(PIN_IR_RIGHT, GPIO_MODE_INPUT);
    gpio_set_direction(PIN_IR_REAR, GPIO_MODE_INPUT);

    adc1_config_width(ADC_WIDTH_BIT_12);
    adc1_config_channel_atten(ADC1_CHANNEL_2, ADC_ATTEN_DB_11); 
    adc1_config_channel_atten(ADC1_CHANNEL_3, ADC_ATTEN_DB_11); 
    adc1_config_channel_atten(ADC1_CHANNEL_0, ADC_ATTEN_DB_11); 

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
    
    xTaskCreate(imu_heading_task, "imu_task", 4096, NULL, 5, NULL); 
    xTaskCreate(adc_sensor_task, "adc_task", 4096, NULL, 4, NULL); 
}