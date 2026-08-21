"""
Waveshare 4-Channel Industrial RS485 Modbus Relay Driver.
Controls power equipment (pump, master_valve, section_valve, fan, led_light) via Modbus RTU.
"""
from firmware import config
from firmware.drivers.desun_uniwill import calc_crc16

try:
    import machine
except ImportError:
    machine = None


class WaveshareRelayBox:
    """
    Driver for Waveshare 4-Channel Modbus RTU RS485 Industrial Relay Box.
    Supports Function Code 0x05 (Write Single Coil) and 0x0F (Write Multiple Coils).
    """

    def __init__(self, slave_addr=None, uart_id=None):
        self.slave_addr = slave_addr or getattr(config, "SLAVE_ADDR_WAVESHARE_RELAY", 0x05)
        self.uart_id = uart_id or getattr(config, "MODBUS_UART_ID", 1)

        # Actuator states (boolean: True = ON/open, False = OFF/closed)
        self.states = {
            "pump": False,
            "master_valve": False,
            "section_valve": False,
            "fan": False,
            "led_light": False
        }
        self.channel_map = {
            "pump": 0,
            "master_valve": 1,
            "section_valve": 2,
            "fan": 3,
            "led_light": 4
        }
        self._uart = None
        self._init_uart()

    def _init_uart(self):
        if machine is not None and hasattr(machine, "UART"):
            try:
                self._uart = machine.UART(self.uart_id, baudrate=getattr(config, "MODBUS_BAUDRATE", 9600))
            except Exception:
                self._uart = None

    def set_actuator(self, actuator_type: str, state: bool, source: str = "manual") -> dict:
        """
        Sets the state of a specific actuator (true = ON/open, false = OFF/closed).
        Returns state change log dictionary.
        """
        if actuator_type in self.states:
            self.states[actuator_type] = bool(state)
            channel = self.channel_map.get(actuator_type, 0)
            self._write_modbus_coil(channel, state)

        return {
            "actuator_type": actuator_type,
            "state": self.states.get(actuator_type, False),
            "source": source
        }

    def _write_modbus_coil(self, channel: int, state: bool):
        if self._uart is None:
            return

        # Function Code 0x05 (Write Single Coil): 0xFF00 = ON, 0x0000 = OFF
        val_bytes = 0xFF00 if state else 0x0000
        raw = bytes([
            self.slave_addr,
            0x05,
            0x00,
            channel & 0xFF,
            (val_bytes >> 8) & 0xFF,
            val_bytes & 0xFF
        ])
        crc = calc_crc16(raw)
        frame = raw + bytes([crc & 0xFF, (crc >> 8) & 0xFF])
        try:
            self._uart.write(frame)
        except Exception:
            pass

    def get_state(self, actuator_type: str) -> bool:
        return self.states.get(actuator_type, False)

    def get_all_states(self) -> dict:
        return dict(self.states)
