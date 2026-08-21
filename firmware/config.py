"""
AGRITECH GREENHOUSE - Person A Firmware Configuration
Centralized configuration parameters, GPIO pin mappings, sensor thresholds, and MQTT settings.
"""

# Board & Identity Configuration
DEVICE_ID = "GREENHOUSE-NODE-A"
NODE_TYPE = "CLIMATE_SOIL_CONTROLLER"
FIRMWARE_VERSION = "1.0.0"

# GPIO Pin Assignments (ESP32 Pinout)
DHT_PIN = 4             # Digital Pin for DHT11 / DHT22
SOIL_ADC_PIN = 34       # Analog ADC Pin for Soil Moisture Sensor
LIGHT_ADC_PIN = 35      # Analog ADC Pin for LDR Light Sensor
ULTRASONIC_TRIG_PIN = 5 # Digital Pin for HC-SR04 Trigger
ULTRASONIC_ECHO_PIN = 18# Digital Pin for HC-SR04 Echo

RELAY_PUMP_PIN = 26     # Relay 1: Water Pump (Irrigation)
RELAY_FAN_PIN = 27      # Relay 2: Cooling Fan (Ventilation)
RELAY_HEATER_PIN = 25   # Relay 3: Heating Mat / Lamp
SERVO_VENT_PIN = 14     # PWM Pin: Roof Vent Hatch Servo Motor

LED_STATUS_PIN = 2      # On-board Status LED
BUZZER_PIN = 13         # Alarm / Alert Buzzer

# Sensor Thresholds & Target Ranges
TEMP_MIN_C = 18.0               # Below this, turn heater ON, close roof vent
TEMP_MAX_C = 28.0               # Above this, turn fan ON, open roof vent
HUMIDITY_MAX_PCT = 80.0         # Above this, turn fan ON to dehumidify

SOIL_MOISTURE_MIN_PCT = 35.0    # Below this, trigger irrigation pump
SOIL_MOISTURE_TARGET_PCT = 65.0 # Stop irrigation pump when target moisture is reached

WATER_TANK_MIN_PCT = 15.0       # Safety limit: refuse pump operation if tank level < 15%
WATER_TANK_MAX_HEIGHT_CM = 50.0 # Tank depth for HC-SR04 level percentage computation
WATER_TANK_SENSOR_OFFSET_CM = 5.0 # Distance from sensor to max fill level

# Timing & Operation Intervals
SENSOR_READ_INTERVAL_MS = 2000    # Read sensors every 2 seconds
TELEMETRY_PUB_INTERVAL_MS = 5000  # Publish MQTT telemetry every 5 seconds
MAX_PUMP_RUN_TIME_SEC = 30        # Maximum consecutive pump runtime safety timeout

# Calibration Data
SOIL_ADC_DRY = 3200     # ADC value in dry soil (0%)
SOIL_ADC_WET = 1200     # ADC value in water/wet soil (100%)
LIGHT_ADC_DARK = 4095   # ADC value in complete darkness
LIGHT_ADC_BRIGHT = 200  # ADC value under direct bright light

# Network & MQTT Settings
WIFI_SSID = "AGRI_GREENHOUSE_WIFI"
WIFI_PASS = "Greenhouse2026!"
WIFI_CONNECT_TIMEOUT_SEC = 15

MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "esp32_person_a"
MQTT_KEEPALIVE = 60

# Modbus RTU / RS485 Configuration (Desun Uniwill & Industrial Relays)
MODBUS_UART_ID = 1
MODBUS_TX_PIN = 17
MODBUS_RX_PIN = 16
MODBUS_BAUDRATE = 9600
DESUN_UNIWILL_SLAVE_ADDR = 0x01

# Desun Uniwill Sensor Plausible Physical Ranges
PH_MIN = 0.0
PH_MAX = 14.0
TDS_MIN = 0.0
TDS_MAX = 3000.0
EC_MIN = 0.0
EC_MAX = 5000.0
WATER_TEMP_MIN = 0.0
WATER_TEMP_MAX = 50.0

# MQTT Topics
MQTT_TOPIC_TELEMETRY = "greenhouse/person_a/telemetry"
MQTT_TOPIC_COMMANDS = "greenhouse/person_a/commands"
MQTT_TOPIC_STATUS = "greenhouse/person_a/status"
MQTT_TOPIC_ALERTS = "greenhouse/person_a/alerts"
