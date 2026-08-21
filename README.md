# AGRITECH GREENHOUSE - ESP32 Modbus RS485 Gateway Firmware & Simulation

Connected Smart Greenhouse Gateway Node (**Person A**) for Environmental Sensing, Water Quality Monitoring, Hydrostatic Tank Tracking, and Waveshare 4-Channel Industrial Relay Control.

Fully compliant with the **"Plateforme d'Automatisation de Serre Intelligente — Catalogue des Données & Flux Applicatifs"** specification.

---

## 📖 Table of Contents
1. [System Overview](#-system-overview)
2. [Data Catalogue Specification & Shared Contract](#-data-catalogue-specification--shared-contract)
3. [Modbus RTU RS485 Hardware Map](#-modbus-rtu-rs485-hardware-map)
4. [Business Rules & Failsafes (RM-1, RM-2, RM-5, RM-7)](#-business-rules--failsafes-rm-1-rm-2-rm-5-rm-7)
5. [FastAPI & WebSocket Communication Flows](#-fastapi--websocket-communication-flows)
6. [Detailed Folder & File Structure](#-detailed-folder--file-structure)
7. [How to Run & Test the Local Simulation](#-how-to-run--test-the-local-simulation)

---

## 🌿 System Overview

The ESP32 Gateway Node (**`GREENHOUSE-PASS-01`**) operates as an industrial **Modbus RTU / RS485 Master**, interrogating 4 slave sensor units cyclically every 5 to 10 seconds and controlling power equipment via a **Waveshare 4-Channel Modbus RS485 Relay Module**.

### 🎯 Key Capabilities
- **Cyclic Modbus RS485 Sensor Polling**: Reads 10 sensor measurements across 4 slave devices.
- **Data Quality Flagging**: Automatically validates measurements against physical plausible bounds and assigns `ok`, `stale`, or `out_of_range`.
- **FastAPI REST Telemetry & Offline Buffer**: Posts telemetry batches to `/api/v1/readings/batch` with `X-Device-Key` header; caches readings in a bounded circular buffer (1000 items) during network outages for catch-up transmission upon reconnection.
- **Automated Rules & Failsafes**: Implements temperature hysteresis ventilation (`RM-1`), low reservoir warning & auto-fill (`RM-2`), scheduled valve control (`RM-5`), and overflow pump lockout (`RM-7`).

---

## 📋 Data Catalogue Specification & Shared Contract

A central JSON Schema contract is maintained in [`shared/data_catalogue_schema.json`](shared/data_catalogue_schema.json) for shared data interoperability between the ESP32 Gateway, FastAPI Backend, and Flutter Mobile App.

### 1. Sensor Data Inventory (Inputs)

| Code (`sensor_type`) | Measured Quantity | Unit | Plausible Range | Modbus Slave Device | Address |
|---|---|---|---|---|---|
| **`ph`** | Water pH | pH | `0.0 – 14.0` | Desun Uniwill | `0x01` |
| **`tds`** | Total Dissolved Solids | ppm | `0.0 – 3000.0` | Desun Uniwill | `0x01` |
| **`ec`** | Electrical Conductivity | uS/cm | `0.0 – 5000.0` | Desun Uniwill | `0x01` |
| **`water_temp`** | Water Temperature | °C | `0.0 – 50.0` | Desun Uniwill | `0x01` |
| **`indoor_temp`** | Indoor Climate Temperature | °C | `-10.0 – 60.0` | Louvered Box | `0x02` |
| **`humidity`** | Indoor Relative Humidity | %RH | `0.0 – 100.0` | Louvered Box | `0x02` |
| **`pressure`** | Atmospheric Pressure | hPa | `900.0 – 1100.0` | Louvered Box | `0x02` |
| **`light`** | Light Intensity | lux | `0.0 – 100000.0` | Louvered Box | `0x02` |
| **`outdoor_temp`** | Outdoor Ambient Temp | °C | `-20.0 – 55.0` | Greenhouse Sensor | `0x03` |
| **`reservoir_height`** | Tank Water Level Height | cm | `0.0 – 100.0` | Hydrostatic Sensor | `0x04` |

**Common record fields**: `device_id`, `sensor_type`, `value`, `quality_flag` (`ok` / `stale` / `out_of_range`), `recorded_at`.

---

### 2. Actuator Data Inventory (Outputs)

| Code (`actuator_type`) | Equipment | State Type | Allowed Sources | Business Constraint |
|---|---|---|---|---|
| **`pump`** | Electric Water Pump | boolean | `manual`, `rule:RM-2`, `rule:RM-5`, `failsafe:RM-7` | Auto-fill on critical low (5cm); lockout on overflow (95cm). |
| **`master_valve`** | Solenoid Master Valve (1") | boolean | `manual`, `rule:RM-5` | Main irrigation line control. |
| **`section_valve`** | Solenoid Section Valve (3/4") | boolean | `manual`, `rule:RM-5` | Zone distribution valve. |
| **`fan`** | AC Ventilation Fan | boolean | `manual`, `rule:RM-1` | Hysteresis band (ON >= 30.0°C, OFF <= 28.0°C). |
| **`led_light`** | Osram LED Lighting | boolean | `manual`, `rule:RM-4`, `rule:RM-5` | Supplemental grow lights / PIR motion. |

**Common record fields**: `device_id`, `actuator_type`, `state` (boolean), `source`, `changed_at`.

---

## ⚙️ Business Rules & Failsafes

- **RM-1 (Fan Temperature Hysteresis)**:
  - Turns `fan` **ON** when `indoor_temp >= 30.0 °C`.
  - Turns `fan` **OFF** when `indoor_temp <= 28.0 °C` (prevents relay chattering).
- **RM-2 (Low Reservoir Warning & Auto-Fill)**:
  - When `reservoir_height <= 15.0 cm`, triggers `low_reservoir_warning` alert and starts 5-minute timer (`RESPONSE_TIMEOUT = 300s`).
  - If no manual intervention and level reaches `critical_low_threshold` (5.0 cm), pump starts automatically (`rule:RM-2`) for max `AUTO_FILL_DURATION = 90s`.
  - Manual commands during the warning window preempt and cancel auto-fill.
- **RM-7 (Overflow Protection Failsafe)**:
  - When `reservoir_height >= 95.0 cm`, pump is locked **OFF** (`failsafe:RM-7`) and `reservoir_overflow_risk` / `pump_failsafe` critical alerts are emitted.
  - Manual "Pump ON" commands during overflow lockout are rejected with reason `"protection anti-débordement"`.

---

## 📂 Detailed Folder & File Structure

```
AGRITECH-GREEN-HOUSE/
├── README.md                            # Comprehensive system documentation
├── setup_env.sh                         # Automated test runner script
├── shared/
│   └── data_catalogue_schema.json       # JSON Schema contract shared with Backend & Mobile App
│
├── firmware/                            # ESP32 MicroPython Firmware
│   ├── boot.py                          # Boot sequence & memory management
│   ├── config.py                        # Modbus UART, slave addresses, thresholds, API endpoints
│   ├── main.py                          # GreenhouseGatewayApp main execution loop
│   │
│   ├── controllers/
│   │   └── climate_controller.py        # Rule Engine (RM-1, RM-2, RM-5, RM-7 state machine)
│   │
│   ├── drivers/                         # Modbus RTU / RS485 Drivers
│   │   ├── desun_uniwill.py             # Desun Uniwill 4-in-1 driver (pH, TDS, EC, water_temp)
│   │   ├── louvered_box.py              # Louvered Box driver (indoor_temp, humidity, pressure, light)
│   │   ├── greenhouse_sensor.py         # Outdoor temperature driver (outdoor_temp)
│   │   ├── hydrostatic_sensor.py        # Hydrostatic water depth driver (reservoir_height)
│   │   └── waveshare_relay.py           # Waveshare 4-channel industrial relay box driver
│   │
│   ├── services/
│   │   ├── mqtt_service.py              # MQTT communication service
│   │   ├── network.py                   # Wi-Fi connection manager
│   │   └── telemetry_service.py         # FastAPI REST batch sender & circular offline buffer
│   │
│   └── utils/
│       └── logger.py                    # Formatted logging utility
│
├── sim/                                 # PC Simulation Environment
│   ├── run_simulation.py                # Interactive CLI simulation dashboard
│   ├── sensor_simulator.py              # Physical digital twin environment physics simulator
│   ├── mqtt_broker_mock.py              # Virtual MQTT broker mock
│   └── micropython_mock/                # MicroPython hardware library mocks (machine, dht, etc.)
│
└── tests/
    └── test_firmware.py                 # Automated unit test suite (7 tests)
```

---

## 🚀 How to Run & Test the Local Simulation

You can test the entire Modbus RS485 Gateway and Rule Engine on your PC without physical hardware!

### Step 1: Run Automated Unit Tests
To verify all Modbus drivers, CRC16 calculations, and RM-1/RM-2/RM-7 rule logic:
```bash
python3 -m unittest tests/test_firmware.py -v
```

### Step 2: Launch Interactive Simulation Dashboard
Run the interactive CLI dashboard:
```bash
python3 sim/run_simulation.py
```

#### Interactive Simulation Keys:
- **`[1]`**: Simulate Low Water Warning (12 cm) -> Triggers `low_reservoir_warning` alert.
- **`[2]`**: Simulate Critical Low Water Auto-Fill (3 cm) -> Triggers RM-2 automatic timed pump fill.
- **`[3]`**: Simulate Overflow Risk (98 cm) -> Triggers RM-7 pump lockout and rejects manual overrides.
- **`[4]`**: Simulate Indoor Heatwave (32 °C) -> Triggers RM-1 fan cooling.
- **`[5]`**: Reset Reservoir to Normal (50 cm).
- **`[m]`**: Input manual operator commands (e.g., `pump ON`, `fan ON`, `mode MANUAL`).
- **`[q]`**: Exit simulation.
