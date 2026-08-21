"""
Servo Motor Driver Module for Roof Hatch / Ventilation Window Control.
"""
try:
    import machine
except ImportError:
    pass

class ServoMotor:
    def __init__(self, pin_num, name="VentServo", freq=50):
        self.pin_num = pin_num
        self.name = name
        self.freq = freq
        self.current_angle = 0
        self._pwm = None
        self._init_pwm()

    def _init_pwm(self):
        try:
            pin = machine.Pin(self.pin_num, machine.Pin.OUT)
            self._pwm = machine.PWM(pin, freq=self.freq)
            self.set_angle(0) # Closed by default
        except Exception:
            self._pwm = None

    def set_angle(self, angle):
        """
        Sets servo position from 0 to 180 degrees.
        Duty cycle for standard 50Hz SG90/MG995 servo:
        - 0 deg   ~ 0.5ms pulse (approx 2.5% duty -> u16 duty 1638..3276)
        - 180 deg ~ 2.5ms pulse (approx 12.5% duty -> u16 duty 8192)
        """
        angle = max(0, min(180, angle))
        self.current_angle = angle

        if self._pwm is not None:
            try:
                # Calculate 16-bit duty (0-65535) for MicroPython ESP32 PWM
                # 0.5ms (duty_u16 ~ 1638) to 2.5ms (duty_u16 ~ 8192)
                duty_u16 = int(1638 + (angle / 180.0) * (8192 - 1638))
                if hasattr(self._pwm, "duty_u16"):
                    self._pwm.duty_u16(duty_u16)
                elif hasattr(self._pwm, "duty"):
                    duty_10bit = int(duty_u16 / 64) # 0-1023 range
                    self._pwm.duty(duty_10bit)
            except Exception:
                pass

    def open_vent(self):
        self.set_angle(90) # Open 90 degrees

    def close_vent(self):
        self.set_angle(0)  # Close 0 degrees

    def get_angle(self):
        return self.current_angle
