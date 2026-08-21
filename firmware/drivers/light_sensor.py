"""
Analog Light (LDR) Sensor Driver.
"""
try:
    import machine
except ImportError:
    pass

class LightSensor:
    def __init__(self, pin_num, dark_val=4095, bright_val=200):
        self.pin_num = pin_num
        self.dark_val = dark_val
        self.bright_val = bright_val
        self.last_pct = 75.0
        self._adc = None
        self._init_sensor()

    def _init_sensor(self):
        try:
            pin = machine.Pin(self.pin_num, machine.Pin.IN)
            self._adc = machine.ADC(pin)
            if hasattr(self._adc, "atten"):
                self._adc.atten(machine.ADC.ATTN_11DB)
        except Exception:
            self._adc = None

    def read_raw(self):
        if self._adc is not None:
            try:
                if hasattr(self._adc, "read_u16"):
                    return self._adc.read_u16() >> 4
                return self._adc.read()
            except Exception:
                pass
        return 1000

    def read_percentage(self):
        """
        Reads light intensity as percentage (0% complete dark, 100% full sunlight).
        """
        raw = self.read_raw()
        if self.dark_val == self.bright_val:
            return 50.0
        pct = (self.dark_val - raw) / float(self.dark_val - self.bright_val) * 100.0
        pct = max(0.0, min(100.0, pct))
        self.last_pct = round(pct, 1)
        return self.last_pct
