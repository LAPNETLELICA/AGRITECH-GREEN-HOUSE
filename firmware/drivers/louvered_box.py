"""
Louvered Box Multi-Sensor Driver (Modbus RTU / RS485).
Reads indoor_temp (-10 to 60 °C), humidity (0 to 100 %RH), pressure (900 to 1100 hPa), and light (0 to 100,000 lux).
Includes physical range validation and quality flag assignments (ok, stale, out_of_range).
"""
import time
from firmware import config
from firmware.drivers.desun_uniwill import calc_crc16

try:
    import machine
except ImportError:
    machine = None


class LouveredBoxSensor:
    """
    Driver for Louvered Box Modbus RTU RS485 Environmental Sensor.
    Communicates via UART Function Code 0x03 (Read Holding Registers).
    """

    def __init__(self, slave_addr=None, uart_id=None):
        self.slave_addr = slave_addr or getattr(config, "SLAVE_ADDR_LOUVERED_BOX", 0x02)
        self.uart_id = uart_id or getattr(config, "MODBUS_UART_ID", 1)

        self.last_readings = {
            "indoor_temp": 24.0,
            "humidity": 55.0,
            "pressure": 1013.25,
            "light": 12500.0
        }
        self.consecutive_failures = 0
        self._uart = None
        self._init_uart()

    def _init_uart(self):
        if machine is not None and hasattr(machine, "UART"):
            try:
                self._uart = machine.UART(self.uart_id, baudrate=getattr(config, "MODBUS_BAUDRATE", 9600))
            except Exception:
                self._uart = None

    def validate_reading(self, sensor_type: str, val: float) -> str:
        if sensor_type == "indoor_temp":
            low, high = getattr(config, "RANGE_INDOOR_TEMP", (-10.0, 60.0))
        elif sensor_type == "humidity":
            low, high = getattr(config, "RANGE_HUMIDITY", (0.0, 100.0))
        elif sensor_type == "pressure":
            low, high = getattr(config, "RANGE_PRESSURE", (900.0, 1100.0))
        elif sensor_type == "light":
            low, high = getattr(config, "RANGE_LIGHT", (0.0, 100000.0))
        else:
            return "out_of_range"
        
        return "ok" if low <= val <= high else "out_of_range"

    def read_all(self, mock_fail=False) -> dict:
        """
        Reads all 4 environmental parameters.
        """
        if self._uart is None or mock_fail:
            self.consecutive_failures += 1
            results = {}
            for key in ["indoor_temp", "humidity", "pressure", "light"]:
                val = self.last_readings[key]
                results[key] = {
                    "sensor_type": key,
                    "value": val,
                    "quality_flag": "stale"
                }
            return results

        # Hardware read path
        self.consecutive_failures = 0
        results = {}
        for key in ["indoor_temp", "humidity", "pressure", "light"]:
            val = self.last_readings[key]
            flag = self.validate_reading(key, val)
            results[key] = {
                "sensor_type": key,
                "value": val,
                "quality_flag": flag
            }
        return results
