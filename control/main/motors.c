#include "robot_config.h"
#include "motors.h"

static const char *TAG = "MOTORS";

const int motor_pwm_gpio[NUM_MOTORS] = {6, 5, 8, 7};
const int encoder_gpio[NUM_MOTORS]   = {11, 9, 13, 12};
const int motor_ina_gpio[NUM_MOTORS] = {20, 19, 47, 21}; 
const int motor_inb_gpio[NUM_MOTORS] = {42, 41, 38, 2}; 

static volatile uint32_t pulse_count[NUM_MOTORS] = {0};
static uint64_t last_eval_time[NUM_MOTORS] = {0};  
static portMUX_TYPE spinlock = portMUX_INITIALIZER_UNLOCKED; 
static float filtered_omega[NUM_MOTORS] = {0, 0, 0, 0};

typedef struct { pid_ctrl_block_handle_t pid; } motor_ctx_t;
static motor_ctx_t motors[NUM_MOTORS];

typedef struct { int index; } encoder_ctx_t;
static encoder_ctx_t enc_ctx[NUM_MOTORS];

static bool encoder_capture_callback(mcpwm_cap_channel_handle_t cap_chan, const mcpwm_capture_event_data_t *edata, void *user_data) {
    encoder_ctx_t *ctx = (encoder_ctx_t *)user_data;
    pulse_count[ctx->index]++;
    return false;
}

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
            raw_omega = (pulses / ENCODER_CPR) * (2.0f * M_PI / dt_sec); 
        }

        filtered_omega[i] = (0.6f * filtered_omega[i]) + (0.4f * raw_omega); 
        
        float target_abs = fabs(target_speed_rads[i]); 
        int dir = (target_speed_rads[i] >= 0.0f) ? 1 : 0;
        float output_pwm = 0;

        if (target_abs == 0.0f) {
            gpio_set_level(motor_ina_gpio[i], 0); 
            gpio_set_level(motor_inb_gpio[i], 0);
            pid_compute(motors[i].pid, 0, &output_pwm); 
            output_pwm = PWM_MAX_DUTY; 
        } else {
            if (i == 0 || i == 1) { 
                gpio_set_level(motor_ina_gpio[i], dir == 1 ? 0 : 1);
                gpio_set_level(motor_inb_gpio[i], dir == 1 ? 1 : 0);
            } else { 
                gpio_set_level(motor_ina_gpio[i], dir == 1 ? 1 : 0);
                gpio_set_level(motor_inb_gpio[i], dir == 1 ? 0 : 1);
            }

            float error = target_abs - filtered_omega[i]; 
            pid_compute(motors[i].pid, error, &output_pwm); 
            
            if (output_pwm < 0) output_pwm = 0;
            if (output_pwm > PWM_MAX_DUTY) output_pwm = PWM_MAX_DUTY;
        }

        ledc_set_duty(LEDC_LOW_SPEED_MODE, (ledc_channel_t)i, (uint32_t)output_pwm);
        ledc_update_duty(LEDC_LOW_SPEED_MODE, (ledc_channel_t)i);
    }

    // ==========================================================
    // TELEMETRÍA ESP-NOW (Enviada cada 50ms al terminar el cálculo PID)
    // ==========================================================
    if (pc_mac_address[0] != 0xFF) {
        telemetry_data_t telem;
        telem.yaw = current_yaw;
        telem.omega[0] = filtered_omega[0];
        telem.omega[1] = filtered_omega[1];
        telem.omega[2] = filtered_omega[2];
        telem.omega[3] = filtered_omega[3];
        
        // Se disparan los 20 bytes exactos al aire hacia tu Dongle/MATLAB
        esp_now_send(pc_mac_address, (uint8_t *)&telem, sizeof(telemetry_data_t));
    }
}

void init_motors(void) {
    for (int i = 0; i < NUM_MOTORS; i++) {
        gpio_reset_pin(motor_ina_gpio[i]); 
        gpio_set_direction(motor_ina_gpio[i], GPIO_MODE_OUTPUT);
        gpio_reset_pin(motor_inb_gpio[i]); 
        gpio_set_direction(motor_inb_gpio[i], GPIO_MODE_OUTPUT);
    }

    ledc_timer_config_t ledc_timer = {
        .speed_mode = LEDC_LOW_SPEED_MODE, .duty_resolution = PWM_RESOLUTION,
        .timer_num = LEDC_TIMER_0, .freq_hz = PWM_FREQUENCY, .clk_cfg = LEDC_AUTO_CLK
    };
    ledc_timer_config(&ledc_timer); 

    for (int i = 0; i < NUM_MOTORS; i++) {
        ledc_channel_config_t ledc_channel = {
            .speed_mode = LEDC_LOW_SPEED_MODE, .channel = (ledc_channel_t)i, 
            .timer_sel = LEDC_TIMER_0, .intr_type = LEDC_INTR_DISABLE, 
            .gpio_num = motor_pwm_gpio[i], .duty = 0, .hpoint = 0
        };
        ledc_channel_config(&ledc_channel); 
    }

    mcpwm_cap_timer_handle_t cap_timer0 = NULL, cap_timer1 = NULL; 
    mcpwm_capture_timer_config_t t_conf0 = { .group_id = 0 }, t_conf1 = { .group_id = 1 };
    mcpwm_new_capture_timer(&t_conf0, &cap_timer0);
    mcpwm_new_capture_timer(&t_conf1, &cap_timer1);

    for (int i = 0; i < NUM_MOTORS; i++) {
        enc_ctx[i].index = i;
        mcpwm_capture_channel_config_t ch_conf = {
            .gpio_num = encoder_gpio[i], .prescale = 1,
            .flags.pos_edge = true, .flags.pull_up = true 
        };
        mcpwm_cap_channel_handle_t cap_chan = NULL;
        mcpwm_new_capture_channel((i < 2) ? cap_timer0 : cap_timer1, &ch_conf, &cap_chan);
        mcpwm_capture_event_callbacks_t cbs = { .on_cap = encoder_capture_callback };
        mcpwm_capture_channel_register_event_callbacks(cap_chan, &cbs, &enc_ctx[i]);
        mcpwm_capture_channel_enable(cap_chan);
    }

    mcpwm_capture_timer_enable(cap_timer0);
    mcpwm_capture_timer_start(cap_timer0);
    mcpwm_capture_timer_enable(cap_timer1);
    mcpwm_capture_timer_start(cap_timer1);

    uint64_t start_time = esp_timer_get_time();
    for(int i=0; i<NUM_MOTORS; i++){ last_eval_time[i] = start_time; }

    for (int i = 0; i < NUM_MOTORS; i++) {
        pid_ctrl_parameter_t pid_params = { 
            .kp = 40.0, .ki = 8.0, .kd = 2.0,
            .cal_type = PID_CAL_TYPE_POSITIONAL, 
            .max_output = PWM_MAX_DUTY, .min_output = 0,
            .max_integral = 1000, .min_integral = -1000,
        };
        pid_ctrl_config_t pid_config = { .init_param = pid_params }; 
        pid_new_control_block(&pid_config, &motors[i].pid);
    }

    const esp_timer_create_args_t timer_args = { .callback = pid_loop_cb, .name = "pid_loop" };
    esp_timer_handle_t timer;
    esp_timer_create(&timer_args, &timer);
    esp_timer_start_periodic(timer, PID_LOOP_PERIOD_MS * 1000); 
}