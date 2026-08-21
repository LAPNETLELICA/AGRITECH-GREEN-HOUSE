"""
Analog Soil Moisture Sensor Driver.
"""
try:
    import machine
except ImportError:
    pass

class SoilMoistureSensor:
    def __init__(self, pin_num, dry_val=3200, wet_val=1200):
        self.pin_num = pin_num
        self.dry_val = dry_val
        self.wet_val = wet_val
        self.last_pct = 50.0
        self._adc = None
        self._init_sensor()

    def _init_sensor(self):
        try:
            pin = machine.Pin(self.pin_num, machine.Pin.IN)
            self._adc = machine.ADC(pin)
            if hasattr(self._adc, "atten"):
                self._adc.atten(machine.ADC.ATTN_11DB) # 0-3.3V range
        except Exception:
            self._adc = None

    def read_raw(self):
        if self._adc is not None:
            try:
                if hasattr(self._adc, "read_u16"):
                    return self._adc.read_u16() >> 4 # 12-bit (0-4095)
                return self._adc.read()
            except Exception:
                pass
        return 2200 # Default neutral value if mock/hardware absent

    def read_percentage(self):
        """
        Reads raw ADC value and maps it to 0.0% - 100.0% moisture.
        """
        raw = self.read_raw()
        # Invert scale: higher ADC value usually means dryer soil
        if self.dry_val == self.wet_val:
            return 50.0
        pct = (self.dry_val - raw) / float(self.dry_val - self.wet_val) * 100.0
        pct = max(0.0, min(100.0, pct))
        self.last_pct = round(pct, 1)
        return self.last_pct
