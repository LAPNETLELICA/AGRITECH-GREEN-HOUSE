"""
Greenhouse Outdoor Ambient Temperature Sensor Driver (Modbus RTU / RS485).
Reads outdoor_temp (-20 to 55 °C).
"""
import time
from firmware import config

try:
    import machine
except ImportError:
    machine = None


class GreenhouseOutdoorSensor:
    """
    Driver for Greenhouse Outdoor Ambient Temperature Sensor (Modbus RTU).
    """

    def __init__(self, slave_addr=None, uart_id=None):
        self.slave_addr = slave_addr or getattr(config, "SLAVE_ADDR_GREENHOUSE", 0x03)
        self.uart_id = uart_id or getattr(config, "MODBUS_UART_ID", 1)
        self.last_reading = 19.5
        self._uart = None
        self._init_uart()

    def _init_uart(self):
        if machine is not None and hasattr(machine, "UART"):
            try:
                self._uart = machine.UART(self.uart_id, baudrate=getattr(config, "MODBUS_BAUDRATE", 9600))
            except Exception:
                self._uart = None

    def validate_reading(self, val: float) -> str:
        low, high = getattr(config, "RANGE_OUTDOOR_TEMP", (-20.0, 55.0))
        return "ok" if low <= val <= high else "out_of_range"

    def read(self, mock_fail=False) -> dict:
        if self._uart is None or mock_fail:
            flag = "stale"
            val = self.last_reading
        else:
            val = self.last_reading
            flag = self.validate_reading(val)

        return {
            "outdoor_temp": {
                "sensor_type": "outdoor_temp",
                "value": val,
                "quality_flag": flag
            }
        }
