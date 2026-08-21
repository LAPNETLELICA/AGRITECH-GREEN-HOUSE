# AGRITECH GREENHOUSE - Person A MicroPython Firmware & Local Simulation Environment

Connected Smart Greenhouse node for **Person A** (Climate & Environmental Monitoring & Microclimate Actuation).

---

## 🌿 System Overview

**Person A** is responsible for the core environmental sensing, soil health monitoring, automated irrigation, and microclimate ventilation/heating regulation inside the smart greenhouse.

### 🎯 Key System Capabilities
- **Environmental Sensing**: Real-time acquisition of air temperature, relative humidity, soil moisture, ambient light intensity, and water tank depth.
- **Automated Microclimate Regulation**:
  - **Auto Irrigation**: Automatically triggers the water pump when soil moisture falls below `35.0%` until the target moisture of `65.0%` is achieved.
  - **Water Tank Safety Lock**: Immediately locks out and disables the irrigation pump if the water tank level drops below `15.0%` to prevent dry-run pump damage.
  - **Auto Ventilation & Cooling**: Turns on the cooling fan and opens the roof vent hatch to `90°` when air temperature exceeds `28.0°C` or humidity exceeds `80.0%`.
  - **Auto Heating & Insulation**: Turns on the heating mat and closes the roof vent hatch (`0°`) when air temperature drops below `18.0°C`.
- **Remote Telemetry & Control**: Connects via Wi-Fi and MQTT broker (`greenhouse/person_a/telemetry`, `greenhouse/person_a/commands`, `greenhouse/person_a/alerts`).

---

## 📂 Detailed Folder & File Guide

Below is the complete architectural directory tree along with the specific function and role of every folder and file in the system:

```
AGRITECH-GREEN-HOUSE/
├── .gitignore                       # Specifies untracked files to ignore (bytecode, caches)
├── README.md                        # Primary project documentation & architecture guide
├── requirements.txt                 # Python dependencies for local testing & simulation
├── setup_env.sh                     # Automated setup & test execution bash script
│
├── firmware/                        # MicroPython Firmware (Deploys directly to ESP32 board)
│   ├── boot.py                      # System boot sequence & heap memory garbage collection
│   ├── config.py                    # Centralized GPIO pinout, sensor thresholds, & MQTT settings
│   ├── main.py                      # Main firmware application loop & hardware execution manager
│   │
│   ├── controllers/                 # Automation State Machines & Decision Engines
│   │   └── climate_controller.py    # Microclimate threshold evaluation & safety controller
│   │
│   ├── drivers/                     # Hardware Abstraction Layer (HAL) Sensor & Actuator Drivers
│   │   ├── dht_sensor.py            # DHT11/DHT22 Air Temperature & Humidity driver
│   │   ├── light_sensor.py          # Analog LDR Ambient Light sensor driver
│   │   ├── relay.py                 # Relay driver for Water Pump, Cooling Fan, and Heater
│   │   ├── servo.py                 # Servo Motor driver for roof ventilation hatch (0°-180°)
│   │   ├── soil_sensor.py           # Analog Soil Moisture driver with ADC percentage calibration
│   │   └── ultrasonic.py            # HC-SR04 Ultrasonic water tank fill level driver
│   │
│   ├── services/                    # Networking & Telemetry Communication Layer
│   │   ├── mqtt_service.py          # MQTT publisher (telemetry/alerts) & command listener
│   │   └── network.py               # ESP32 Wi-Fi Station connection manager & reconnect fallback
│   │
│   └── utils/                       # System Utilities
│       └── logger.py                # Dual MicroPython/CPython formatted logging utility
│
├── sim/                             # Local PC Hardware & Physics Simulation (No ESP32 needed!)
│   ├── mqtt_broker_mock.py          # In-memory local MQTT broker & message router
│   ├── run_simulation.py            # Interactive CLI runner & real-time terminal dashboard
│   ├── sensor_simulator.py          # Physical environment simulator (diurnal heat, soil drying)
│   │
│   └── micropython_mock/            # Desktop CPython Compatibility Mocks for MicroPython Libraries
│       ├── dht.py                   # CPython mock for MicroPython 'dht' module
│       ├── machine.py               # CPython mock for MicroPython 'machine' (Pin, ADC, PWM)
│       ├── network.py               # CPython mock for MicroPython 'network' module
│       └── umqtt/
│           ├── __init__.py          # MicroPython umqtt package mock init
│           └── simple.py            # CPython mock for MicroPython 'umqtt.simple.MQTTClient'
│
└── tests/                           # Automated Testing Suite
    └── test_firmware.py             # Unit tests verifying drivers, state machine, & safety locks
```

---

## 🛠️ Detailed File Responsibilities & Functions

### 1. Root Workspace Files
| File | Function & System Role |
|---|---|
| **`README.md`** | Complete system documentation, pinout diagrams, directory descriptions, and user guides. |
| **`requirements.txt`** | Lists optional Python dependencies (`pytest`, `paho-mqtt`) for running simulation tests. |
| **`setup_env.sh`** | Executable shell script that verifies Python installation, executes test suites, and prepares the simulation environment. |
| **`.gitignore`** | Excludes compiled Python bytecode (`__pycache__`) and local test caches from Git commits. |

---

### 2. Firmware Directory (`firmware/`)
*Contains pure MicroPython code ready to deploy onto physical ESP32 microcontrollers via Thonny, esptool, or ampy.*

| File / Folder | Component | Function & Detailed Description |
|---|---|---|
| **`firmware/config.py`** | Configuration | Centralized settings module storing GPIO pin assignments (DHT=4, Soil=34, Relays=25,26,27, Servo=14), temperature thresholds (18.0°C to 28.0°C), soil moisture limits (35.0% - 65.0%), water tank safety cutoff (15.0%), Wi-Fi credentials, and MQTT topics. |
| **`firmware/boot.py`** | Boot Script | System startup script executed first by MicroPython. Initializes hardware heap garbage collection, displays board diagnostics, and sets up debug logging. |
| **`firmware/main.py`** | Main Application | Main entry point that instantiates all hardware drivers, connects Wi-Fi & MQTT, and executes the recurring control cycle (reading sensors -> evaluating automation logic -> updating relays -> publishing telemetry). |
| **`firmware/controllers/climate_controller.py`** | State Machine | Core greenhouse microclimate rule engine. Evaluates sensor telemetry against target thresholds in `AUTO` mode, enforces the low-water safety lock to prevent pump damage, and handles incoming `MANUAL` MQTT control commands. |
| **`firmware/drivers/dht_sensor.py`** | Driver | Interface for DHT11 and DHT22 digital sensors reading ambient temperature (°C) and relative air humidity (%). Includes read smoothing and error handling. |
| **`firmware/drivers/soil_sensor.py`** | Driver | Reads 12-bit analog ADC values (0-4095) from soil moisture probes and converts them into calibrated 0.0% (dry) to 100.0% (wet) soil moisture values. |
| **`firmware/drivers/light_sensor.py`** | Driver | Reads analog light intensity from LDR sensors and maps raw values to ambient sunlight percentages. |
| **`firmware/drivers/ultrasonic.py`** | Driver | Uses HC-SR04 ultrasonic pulse timing (Trigger/Echo) to measure distance to water surface, computing water tank fill percentage based on total tank depth. |
| **`firmware/drivers/relay.py`** | Driver | Manages active-low and active-high relay modules for controlling the Water Pump, Ventilation Fan, and Heating Mat. |
| **`firmware/drivers/servo.py`** | Driver | Generates 50Hz PWM signals to rotate the roof ventilation hatch servo motor between 0° (fully closed) and 90° (fully open). |
| **`firmware/services/network.py`** | Service | Handles ESP32 Wi-Fi station connection (`network.WLAN`), IP address retrieval, and automatic reconnection fallback if Wi-Fi drops. |
| **`firmware/services/mqtt_service.py`** | Service | Handles MQTT client connections, publishes JSON telemetry (`greenhouse/person_a/telemetry`) and system alerts, and subscribes to remote commands. |
| **`firmware/utils/logger.py`** | Utility | Universal logging module supporting formatted level logs (`[INFO]`, `[WARN]`, `[ERROR]`, `[DEBUG]`) with automatic timestamp handling for MicroPython (`ticks_ms`) and standard Python. |

---

### 3. Simulation Directory (`sim/`)
*Allows running and testing Person A firmware locally on any PC (Linux/macOS/Windows) without requiring physical hardware.*

| File / Folder | Component | Function & Detailed Description |
|---|---|---|
| **`sim/micropython_mock/machine.py`** | Hardware Mock | Emulates MicroPython's `machine` module (`Pin`, `ADC`, `PWM`, `RTC`, `WDT`) so firmware files import hardware classes seamlessly on desktop CPython. |
| **`sim/micropython_mock/dht.py`** | Sensor Mock | Emulates MicroPython's `dht` module (`DHT11`, `DHT22`) allowing simulated temperature and humidity injection. |
| **`sim/micropython_mock/network.py`** | Network Mock | Emulates MicroPython's `network.WLAN` interface for local PC execution. |
| **`sim/micropython_mock/umqtt/simple.py`** | MQTT Mock | Emulates MicroPython's `umqtt.simple.MQTTClient`, routing messages directly to the in-memory simulation broker. |
| **`sim/sensor_simulator.py`** | Physics Model | Simulates dynamic greenhouse physics over time: diurnal solar heating cycles, evapotranspiration soil drying, irrigation pump soil moistening, and water tank depletion. |
| **`sim/mqtt_broker_mock.py`** | Message Broker | Built-in lightweight in-memory MQTT broker routing published telemetry and subscribed commands without requiring external Mosquitto installation. |
| **`sim/run_simulation.py`** | CLI Dashboard | Interactive terminal application displaying a real-time dashboard with live sensor gauges, actuator indicators, MQTT logs, and interactive trigger keys (`[1]` Dry Soil, `[2]` Heatwave, `[4]` Empty Tank). |

---

### 4. Tests Directory (`tests/`)
| File | Function & System Role |
|---|---|
| **`tests/test_firmware.py`** | Suite of 9 automated unit tests verifying relay driver states, servo pulse duty calculations, soil ADC calibration, climate threshold state transitions, safety lockouts, and MQTT command handlers using `unittest`/`pytest`. |

---

## 🔌 Hardware Pinout Mapping (ESP32)

| Component | ESP32 Pin | Type | Function |
|---|---|---|---|
| **DHT22 / DHT11** | GPIO 4 | Digital Input | Air Temperature & Humidity Sensor |
| **Soil Moisture** | GPIO 34 | Analog (ADC1_CH6) | Soil Moisture Probe (0 - 3.3V) |
| **Light Sensor (LDR)** | GPIO 35 | Analog (ADC1_CH7) | Ambient Light Intensity Sensor |
| **HC-SR04 Trigger** | GPIO 5 | Digital Output | Ultrasonic Tank Sensor Trigger |
| **HC-SR04 Echo** | GPIO 18 | Digital Input | Ultrasonic Tank Sensor Echo |
| **Irrigation Pump Relay**| GPIO 26 | Digital Output | Water Pump Relay (Active Low) |
| **Cooling Fan Relay** | GPIO 27 | Digital Output | Ventilation Fan Relay |
| **Heating Mat Relay** | GPIO 25 | Digital Output | Heat Lamp / Mat Relay |
| **Vent Hatch Servo** | GPIO 14 | PWM (50Hz) | Roof Vent Position Control (0°-180°) |
| **Status LED** | GPIO 2 | Digital Output | On-board Status / Heartbeat Indicator |

---

## 📡 MQTT Topics & JSON Payload Schema

### 1. Telemetry Broadcast (`greenhouse/person_a/telemetry`)
Published periodically (every 5 seconds):
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

### 2. Commands Listener (`greenhouse/person_a/commands`)
Subscribed control commands:
- **Set Mode**: `{"action": "SET_MODE", "value": "AUTO"}` or `{"action": "SET_MODE", "value": "MANUAL"}`
- **Manual Actuator Overrides**:
  - Pump: `{"action": "PUMP", "value": "ON"}` | `{"action": "PUMP", "value": "OFF"}`
  - Fan: `{"action": "FAN", "value": "ON"}` | `{"action": "FAN", "value": "OFF"}`
  - Heater: `{"action": "HEATER", "value": "ON"}` | `{"action": "HEATER", "value": "OFF"}`
  - Roof Vent Angle: `{"action": "VENT", "value": 45}`

---

## 🚀 How to Run the Local Simulation

### 1. Execute Setup & Automated Tests
```bash
chmod +x setup_env.sh
./setup_env.sh
```

### 2. Launch Interactive Terminal Dashboard
```bash
python3 sim/run_simulation.py
```

#### Interactive Console Action Keys:
- **`[1]`**: Simulate dry soil (<35%) -> Triggers automatic irrigation pump.
- **`[2]`**: Simulate heatwave (>30°C) -> Triggers cooling fan & opens roof vent hatch.
- **`[3]`**: Simulate cold drop (<18°C) -> Triggers heating mat & closes roof vent.
- **`[4]`**: Empty water tank (<15%) -> Triggers low-water safety lock (disables pump).
- **`[5]`**: Refill water tank (100%).
- **`[m]`**: Send manual MQTT override commands.
- **`[q]`**: Exit simulation.
