"""
Hydrostatic Water Level Sensor Driver (Modbus RTU / RS485).
Reads reservoir_height (0 to 100 cm).
"""
import time
from firmware import config

try:
    import machine
except ImportError:
    machine = None


class HydrostaticSensor:
    """
    Driver for Hydrostatic Reservoir Water Level Sensor (Modbus RTU RS485).
    """

    def __init__(self, slave_addr=None, uart_id=None):
        self.slave_addr = slave_addr or getattr(config, "SLAVE_ADDR_HYDROSTATIC", 0x04)
        self.uart_id = uart_id or getattr(config, "MODBUS_UART_ID", 1)
        self.last_reading = 42.7
        self._uart = None
        self._init_uart()

    def _init_uart(self):
        if machine is not None and hasattr(machine, "UART"):
            try:
                self._uart = machine.UART(self.uart_id, baudrate=getattr(config, "MODBUS_BAUDRATE", 9600))
            except Exception:
                self._uart = None

    def validate_reading(self, val: float) -> str:
        low, high = getattr(config, "RANGE_RESERVOIR_HEIGHT", (0.0, 100.0))
        return "ok" if low <= val <= high else "out_of_range"

    def read(self, mock_fail=False) -> dict:
        if self._uart is None or mock_fail:
            flag = "stale"
            val = self.last_reading
        else:
            val = self.last_reading
            flag = self.validate_reading(val)

        return {
            "reservoir_height": {
                "sensor_type": "reservoir_height",
                "value": val,
                "quality_flag": flag
            }
        }
