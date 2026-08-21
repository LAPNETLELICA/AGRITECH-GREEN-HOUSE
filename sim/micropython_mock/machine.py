"""
MicroPython 'machine' module mock for desktop CPython simulation.
"""
import time

class Pin:
    IN = 0
    OUT = 1
    PULL_UP = 2
    PULL_DOWN = 3

    _pin_states = {}

    def __init__(self, pin_number, mode=IN, pull=-1):
        self.pin_number = pin_number
        self.mode = mode
        self.pull = pull
        if pin_number not in Pin._pin_states:
            Pin._pin_states[pin_number] = 0

    def value(self, val=None):
        if val is not None:
            Pin._pin_states[self.pin_number] = 1 if val else 0
        return Pin._pin_states.get(self.pin_number, 0)

    def on(self):
        self.value(1)

    def off(self):
        self.value(0)

class ADC:
    ATTN_0DB = 0
    ATTN_2_5DB = 1
    ATTN_6DB = 2
    ATTN_11DB = 3

    _adc_values = {}

    def __init__(self, pin):
        self.pin = pin
        self.pin_number = pin.pin_number if hasattr(pin, "pin_number") else int(pin)
        if self.pin_number not in ADC._adc_values:
            ADC._adc_values[self.pin_number] = 2048

    def atten(self, attenuation):
        pass

    def width(self, bits):
        pass

    def read(self):
        return ADC._adc_values.get(self.pin_number, 2048)

    def read_u16(self):
        val_12bit = self.read()
        return val_12bit << 4

    @classmethod
    def set_mock_value(cls, pin_number, val_12bit):
        cls._adc_values[pin_number] = max(0, min(4095, int(val_12bit)))

class PWM:
    _pwm_duties = {}

    def __init__(self, pin, freq=50, duty=0):
        self.pin = pin
        self.pin_number = pin.pin_number if hasattr(pin, "pin_number") else int(pin)
        self._freq = freq
        self.duty(duty)

    def freq(self, f=None):
        if f is not None:
            self._freq = f
        return self._freq

    def duty(self, d=None):
        if d is not None:
            PWM._pwm_duties[self.pin_number] = d
        return PWM._pwm_duties.get(self.pin_number, 0)

    def duty_u16(self, d_u16=None):
        if d_u16 is not None:
            duty_10bit = int(d_u16 / 64)
            return self.duty(duty_10bit)
        return self.duty() * 64

    def deinit(self):
        pass

class RTC:
    def __init__(self):
        pass
    def datetime(self, tuple_val=None):
        t = time.localtime()
        return (t.tm_year, t.tm_mon, t.tm_mday, t.tm_wday, t.tm_hour, t.tm_min, t.tm_sec, 0)

class WDT:
    def __init__(self, id=0, timeout=5000):
        pass
    def feed(self):
        pass

def reset():
    print("[MOCK machine] Hardware reset triggered.")

def time_pulse_us(pin, pulse_level, timeout_us=30000):
    return 1000 # Mock echo pulse duration
