"""
AGRITECH GREENHOUSE - Central Configuration & Specification Constants
Platform Automation Specification (Data Catalogue & Application Flows)
"""

# Board & Identity Configuration
DEVICE_ID = "GREENHOUSE-PASS-01"
NODE_TYPE = "MODBUS_ESP32_GATEWAY"
FIRMWARE_VERSION = "2.0.0"

# RS485 / Modbus RTU Master UART Configuration
MODBUS_UART_ID = 1
MODBUS_TX_PIN = 17
MODBUS_RX_PIN = 16
MODBUS_DE_RE_PIN = 4    # RS485 Direction Control Pin
MODBUS_BAUDRATE = 9600

# Modbus Slave Addresses (4 Sensors + 1 Waveshare Relay Box)
SLAVE_ADDR_DESUN_UNIWILL = 0x01
SLAVE_ADDR_LOUVERED_BOX  = 0x02
SLAVE_ADDR_GREENHOUSE    = 0x03
SLAVE_ADDR_HYDROSTATIC   = 0x04
SLAVE_ADDR_WAVESHARE_RELAY = 0x05

# Sensor Plausible Physical Ranges (Section 2 Specification)
RANGE_PH = (0.0, 14.0)               # pH
RANGE_TDS = (0.0, 3000.0)            # ppm
RANGE_EC = (0.0, 5000.0)             # uS/cm
RANGE_WATER_TEMP = (0.0, 50.0)       # °C
RANGE_INDOOR_TEMP = (-10.0, 60.0)    # °C
RANGE_HUMIDITY = (0.0, 100.0)        # %RH
RANGE_PRESSURE = (900.0, 1100.0)     # hPa
RANGE_LIGHT = (0.0, 100000.0)        # lux
RANGE_OUTDOOR_TEMP = (-20.0, 55.0)   # °C
RANGE_RESERVOIR_HEIGHT = (0.0, 100.0)# cm

# Business Rule Parameters (RM-1, RM-2, RM-5, RM-7)
# RM-1: Fan Hysteresis (ON at 30.0°C, OFF at 28.0°C)
FAN_TEMP_ON_C = 30.0
FAN_TEMP_OFF_C = 28.0

# RM-2 & RM-7: Reservoir Water Level Management & Pump Protection
RESERVOIR_MAX_HEIGHT_CM = 100.0
RESERVOIR_OVERFLOW_THRESHOLD_CM = 95.0 # RM-7: Pump lockout threshold
RESERVOIR_HIGH_THRESHOLD_CM = 85.0     # High level warning threshold
RESERVOIR_LOW_THRESHOLD_CM = 15.0      # Low level warning threshold
RESERVOIR_CRITICAL_LOW_CM = 5.0        # RM-2: Critical threshold triggering auto fill

RESPONSE_TIMEOUT_SEC = 300            # 5 min user response window before auto-fill
AUTO_FILL_DURATION_SEC = 90           # Maximum auto-fill runtime limit

# Polling & Telemetry Intervals
POLLING_CYCLE_SEC = 5.0               # 5-10 second Modbus polling cycle (HI-7)
HEARTBEAT_INTERVAL_SEC = 30.0
MAX_OFFLINE_BUFFER_SIZE = 1000        # Circular buffer capacity for offline catch-up

# Network & FastAPI Backend REST Endpoints
WIFI_SSID = "AGRI_GREENHOUSE_WIFI"
WIFI_PASS = "Greenhouse2026!"
WIFI_CONNECT_TIMEOUT_SEC = 15
DEVICE_API_KEY = "DEV_KEY_ESP32_PASS_01_SECRET"

FASTAPI_BASE_URL = "http://127.0.0.1:8000"
ENDPOINT_READINGS_BATCH = "/api/v1/readings/batch"
ENDPOINT_ACTUATOR_STATE = "/api/v1/actuators/{id}/state"
ENDPOINT_ALERTS = "/api/v1/alerts"
ENDPOINT_HEARTBEAT = "/api/v1/devices/{id}/heartbeat"
ENDPOINT_WS = "ws://127.0.0.1:8000/api/v1/ws"
