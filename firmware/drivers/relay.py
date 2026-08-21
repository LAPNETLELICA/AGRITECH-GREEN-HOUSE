"""
Relay Actuator Driver Module.
Supports active-high and active-low relay modules for Pump, Fan, Heater, etc.
"""
try:
    import machine
except ImportError:
    pass

class Relay:
    def __init__(self, pin_num, name="Relay", active_low=True):
        self.pin_num = pin_num
        self.name = name
        self.active_low = active_low
        self._state = False
        self._pin = None
        self._init_pin()

    def _init_pin(self):
        try:
            self._pin = machine.Pin(self.pin_num, machine.Pin.OUT)
            self.off() # Ensure initial OFF state
        except Exception:
            self._pin = None

    def turn_on(self):
        self._state = True
        if self._pin is not None:
            val = 0 if self.active_low else 1
            self._pin.value(val)

    def turn_off(self):
        self._state = False
        if self._pin is not None:
            val = 1 if self.active_low else 0
            self._pin.value(val)

    def on(self):
        self.turn_on()

    def off(self):
        self.turn_off()

    def toggle(self):
        if self._state:
            self.off()
        else:
            self.on()

    def is_on(self):
        return self._state

    def status_str(self):
        return "ON" if self._state else "OFF"
