"""
Desun Uniwill 4-in-1 Water Quality Sensor Driver (Modbus RTU / RS485).
Reads pH, Total Dissolved Solids (TDS), Electrical Conductivity (EC), and Water Temperature.
Includes physical range validation and quality flag assignments (ok, stale, out_of_range).
"""
import time
from firmware import config

try:
    import machine
except ImportError:
    machine = None


def calc_crc16(data: bytes) -> int:
    """
    Computes standard Modbus RTU CRC-16 (Polynomial 0xA001).
    """
    crc = 0xFFFF
    for pos in data:
        crc ^= pos
        for _ in range(8):
            if (crc & 0x0001) != 0:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc


class DesunUniwillSensor:
    """
    Driver for Desun Uniwill Modbus RTU RS485 Water Quality Sensor.
    Communicates via UART using Function Code 0x03 (Read Holding Registers).
    """

    def __init__(self, slave_addr=None, uart_id=None, tx_pin=None, rx_pin=None, baudrate=None):
        self.slave_addr = slave_addr or getattr(config, "DESUN_UNIWILL_SLAVE_ADDR", 1)
        self.uart_id = uart_id or getattr(config, "MODBUS_UART_ID", 1)
        self.tx_pin = tx_pin or getattr(config, "MODBUS_TX_PIN", 17)
        self.rx_pin = rx_pin or getattr(config, "MODBUS_RX_PIN", 16)
        self.baudrate = baudrate or getattr(config, "MODBUS_BAUDRATE", 9600)

        # Last known valid readings for stale fallback
        self.last_readings = {
            "ph": 7.0,
            "tds": 450.0,
            "ec": 850.0,
            "water_temp": 22.5
        }
        self.consecutive_failures = 0

        self._uart = None
        self._init_uart()

    def _init_uart(self):
        """Initializes MicroPython hardware UART if available."""
        if machine is not None and hasattr(machine, "UART"):
            try:
                self._uart = machine.UART(
                    self.uart_id,
                    baudrate=self.baudrate,
                    tx=self.tx_pin,
                    rx=self.rx_pin,
                    bits=8,
                    parity=None,
                    stop=1
                )
            except Exception:
                self._uart = None

    def build_read_request(self, start_reg=0x0000, num_regs=4) -> bytes:
        """
        Builds a standard Modbus RTU Function Code 0x03 request frame.
        Frame format: [SlaveAddr, FunctionCode, StartRegHi, StartRegLo, NumRegsHi, NumRegsLo, CRCLo, CRCHi]
        """
        raw = bytes([
            self.slave_addr,
            0x03,
            (start_reg >> 8) & 0xFF,
            start_reg & 0xFF,
            (num_regs >> 8) & 0xFF,
            num_regs & 0xFF
        ])
        crc = calc_crc16(raw)
        return raw + bytes([crc & 0xFF, (crc >> 8) & 0xFF])

    def validate_reading(self, sensor_type: str, val: float) -> str:
        """
        Validates raw reading against physical plausible range.
        Returns quality flag: 'ok' or 'out_of_range'.
        """
        if sensor_type == "ph":
            if config.PH_MIN <= val <= config.PH_MAX:
                return "ok"
        elif sensor_type == "tds":
            if config.TDS_MIN <= val <= config.TDS_MAX:
                return "ok"
        elif sensor_type == "ec":
            if config.EC_MIN <= val <= config.EC_MAX:
                return "ok"
        elif sensor_type == "water_temp":
            if config.WATER_TEMP_MIN <= val <= config.WATER_TEMP_MAX:
                return "ok"
        return "out_of_range"

    def read_hardware_registers(self):
        """
        Sends Modbus RTU request over UART and reads register response.
        Returns dict of raw floats or None if communication fails.
        """
        if self._uart is None:
            return None

        req = self.build_read_request(0x0000, 4)
        try:
            # Clear UART buffer before reading
            if hasattr(self._uart, "any") and self._uart.any():
                self._uart.read()

            self._uart.write(req)
            time.sleep(0.1) # Wait for RS485 slave response

            # Response expected length: 5 header/footer + 2 * 4 bytes data = 13 bytes
            resp = self._uart.read(13)
            if not resp or len(resp) < 13:
                return None

            # Validate Modbus CRC16
            payload = resp[:-2]
            received_crc = resp[-2] | (resp[-1] << 8)
            if calc_crc16(payload) != received_crc:
                return None

            # Check slave address and function code
            if resp[0] != self.slave_addr or resp[1] != 0x03:
                return None

            # Parse register values (big-endian unsigned short)
            ph_raw = (resp[3] << 8) | resp[4]
            tds_raw = (resp[5] << 8) | resp[6]
            ec_raw = (resp[7] << 8) | resp[8]
            temp_raw = (resp[9] << 8) | resp[10]

            return {
                "ph": round(ph_raw / 100.0, 2),
                "tds": float(tds_raw),
                "ec": float(ec_raw),
                "water_temp": round(temp_raw / 10.0, 1)
            }
        except Exception:
            return None

    def read_all(self, mock_fail=False, mock_out_of_range=False) -> dict:
        """
        Reads all 4 water quality parameters (ph, tds, ec, water_temp).
        Returns a dictionary containing value and quality_flag for each sensor_type.
        Quality Flags:
          - 'ok': Reading valid and within plausible physical bounds.
          - 'stale': Communication failed; returning last known good reading.
          - 'out_of_range': Measured value falls outside physical plausible limits.
        """
        # Attempt physical hardware read
        raw_data = None if mock_fail else self.read_hardware_registers()

        if raw_data is None:
            # Hardware absent or read failed
            self.consecutive_failures += 1
            if mock_fail or self.consecutive_failures >= 1:
                # Mark reading as stale
                results = {}
                for key in ["ph", "tds", "ec", "water_temp"]:
                    val = self.last_readings[key]
                    if mock_out_of_range:
                        val = 99.0 if key == "ph" else 9999.0
                        flag = "out_of_range"
                    else:
                        flag = "stale"
                    results[key] = {
                        "sensor_type": key,
                        "value": val,
                        "quality_flag": flag
                    }
                return results

        # Hardware read succeeded
        self.consecutive_failures = 0
        results = {}
        for key in ["ph", "tds", "ec", "water_temp"]:
            val = raw_data[key]
            flag = self.validate_reading(key, val)
            if flag == "ok":
                self.last_readings[key] = val
            results[key] = {
                "sensor_type": key,
                "value": val,
                "quality_flag": flag
            }

        return results
