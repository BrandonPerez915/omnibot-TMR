idf_component_register(
    SRCS "mcpwm_bdc_control_example_main.c"
    INCLUDE_DIRS "."
    PRIV_REQUIRES
        esp_driver_gpio
        esp_driver_ledc
        esp_driver_mcpwm
        esp_timer
        esp_driver_uart    
        esp_driver_i2c
        esp_wifi        # <--- Este ya incluye las funciones de esp_now.h
        esp_netif
        nvs_flash
        driver
)