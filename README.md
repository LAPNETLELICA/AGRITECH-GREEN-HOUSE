# AGRITECH GREENHOUSE - Person A MicroPython Firmware & Local Simulation Environment

Connected Smart Greenhouse node for **Person A** (Climate & Environmental Monitoring & Microclimate Actuation).

---

## 🌿 System Overview

**Person A** is responsible for the core climate sensing, soil health monitoring, automated irrigation, and ventilation control inside the smart greenhouse.

### Key Responsibilities
- **Environmental Sensing**: Real-time acquisition of air temperature, relative humidity, soil moisture, ambient light, and water tank fill level.
- **Microclimate Automation State Machine**:
  - **Auto Irrigation**: Triggers water pump when soil moisture falls below `35.0%` until `65.0%` target is reached.
  - **Water Safety Interlock**: Immediately disables irrigation pump if water tank level drops below `15.0%` safety cutoff.
  - **Auto Ventilation & Cooling**: Turns on cooling fan and opens roof vent hatch (`90°`) when temperature exceeds `28.0°C` or humidity exceeds `80.0%`.
  - **Auto Heating**: Turns on heating mat and closes roof hatch (`0°`) when temperature falls below `18.0°C`.
- **Remote Telemetry & Control**: Connects to Wi-Fi and MQTT broker (`greenhouse/person_a/telemetry`, `greenhouse/person_a/commands`, `greenhouse/person_a/alerts`).

---

## 📁 Directory Architecture

```
AGRITECH-GREEN-HOUSE/
├── firmware/                        # MicroPython Firmware (deploys directly to ESP32)
│   ├── boot.py                      # System boot initialization & memory heap setup
│   ├── main.py                      # Main entry point & hardware execution loop
│   ├── config.py                    # Centralized GPIO pinout, thresholds, and MQTT settings
│   ├── drivers/                     # Modular Hardware Drivers
│   │   ├── dht_sensor.py            # DHT11/DHT22 Air Temp & Humidity driver
│   │   ├── soil_sensor.py           # Analog Capacitive/Resistive Soil Moisture driver
│   │   ├── light_sensor.py          # Analog LDR Ambient Light driver
│   │   ├── ultrasonic.py            # HC-SR04 Water Tank Level driver
│   │   ├── relay.py                 # Relay Actuator driver (Pump, Fan, Heater)
│   │   └── servo.py                 # Vent Roof Servo Motor driver (0° - 180°)
│   ├── controllers/
│   │   └── climate_controller.py    # Microclimate State Machine (AUTO/MANUAL logic)
│   ├── services/
│   │   ├── network.py               # ESP32 Wi-Fi Connection Manager
│   │   └── mqtt_service.py          # Telemetry Publisher & Command Listener
│   └── utils/
│       └── logger.py                # Dual MicroPython/CPython formatted logger
├── sim/                             # Local PC Simulation Environment (No hardware needed!)
│   ├── micropython_mock/            # CPython hardware library mocks
│   │   ├── machine.py               # Pin, ADC, PWM, I2C, WDT mocks
│   │   ├── dht.py                   # DHT11/DHT22 mocks
│   │   ├── network.py               # WLAN interface mock
│   │   └── umqtt/simple.py          # MQTTClient mock
│   ├── sensor_simulator.py          # Physics model (diurnal cycles, drying, irrigation)
│   ├── mqtt_broker_mock.py          # In-memory local MQTT broker
│   └── run_simulation.py            # Interactive CLI runner & live terminal dashboard
├── tests/
│   └── test_firmware.py             # Automated unit test suite (pytest / unittest)
├── setup_env.sh                     # Setup script and launcher
├── requirements.txt                 # Python dependencies
└── README.md                        # Documentation
```

---

## 🔌 Hardware Pinout Mapping (ESP32)

| Component | ESP32 Pin | Type | Function |
|---|---|---|---|
| **DHT22 / DHT11** | GPIO 4 | Digital | Air Temperature & Humidity Sensor |
| **Soil Moisture** | GPIO 34 | Analog (ADC1_CH6) | Soil Moisture Reading (0 - 3.3V) |
| **Light Sensor (LDR)** | GPIO 35 | Analog (ADC1_CH7) | Ambient Light Intensity |
| **HC-SR04 Trigger** | GPIO 5 | Digital Output | Ultrasonic Tank Sensor Trigger |
| **HC-SR04 Echo** | GPIO 18 | Digital Input | Ultrasonic Tank Sensor Echo |
| **Irrigation Pump Relay**| GPIO 26 | Digital Output | Water Pump Relay (Active Low) |
| **Cooling Fan Relay** | GPIO 27 | Digital Output | Ventilation Fan Relay |
| **Heating Mat Relay** | GPIO 25 | Digital Output | Heat Lamp / Mat Relay |
| **Vent Hatch Servo** | GPIO 14 | PWM (50Hz) | Roof Vent Position Control (0°-180°) |
| **Status LED** | GPIO 2 | Digital Output | Board Heartbeat / Status Indicator |

---

## 📡 MQTT Topics & Message Schema

### Telemetry Topic (`greenhouse/person_a/telemetry`)
Published every 5 seconds (JSON format):
```json
{
  "device_id": "GREENHOUSE-NODE-A",
  "node_type": "CLIMATE_SOIL_CONTROLLER",
  "temperature": 24.5,
  "humidity": 58.0,
  "soil_moisture": 42.0,
  "light_intensity": 75.0,
  "water_level": 82.5,
  "mode": "AUTO",
  "actuators": {
    "pump": "OFF",
    "fan": "OFF",
    "heater": "OFF",
    "vent_angle": 0
  },
  "alerts": []
}
```

### Commands Topic (`greenhouse/person_a/commands`)
Subscribe payload options:
- Mode change: `{"action": "SET_MODE", "value": "AUTO"}` or `{"action": "SET_MODE", "value": "MANUAL"}`
- Manual override: `{"action": "PUMP", "value": "ON"}` | `{"action": "FAN", "value": "ON"}` | `{"action": "VENT", "value": 45}`

---

## 🚀 Running the Local Simulation

You can run the full environment on PC without any physical ESP32 or external MQTT server!

### 1. Execute Setup Script
```bash
chmod +x setup_env.sh
./setup_env.sh
```

### 2. Run Automated Unit Tests
```bash
python3 -m unittest tests/test_firmware.py -v
```

### 3. Launch Interactive Terminal Dashboard
```bash
python3 sim/run_simulation.py
```

#### Interactive Simulation Controls:
- Press `1`: Simulate dry soil (<35%) -> Triggers automatic irrigation.
- Press `2`: Simulate heatwave (>30°C) -> Triggers cooling fan & opens vent hatch.
- Press `3`: Simulate temperature drop (<18°C) -> Triggers heating mat.
- Press `4`: Empty water tank (<10%) -> Triggers safety lock (disables pump).
- Press `5`: Refill water tank (100%).
- Press `m`: Send manual MQTT override commands.
- Press `q`: Exit simulation.
