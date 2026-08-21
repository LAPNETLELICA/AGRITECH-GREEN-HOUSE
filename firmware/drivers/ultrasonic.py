"""
HC-SR04 Ultrasonic Water Tank Level Sensor Driver.
"""
import time
try:
    import machine
except ImportError:
    pass

class UltrasonicSensor:
    def __init__(self, trig_pin, echo_pin, max_height_cm=50.0, sensor_offset_cm=5.0):
        self.trig_pin_num = trig_pin
        self.echo_pin_num = echo_pin
        self.max_height_cm = max_height_cm
        self.sensor_offset_cm = sensor_offset_cm
        self.last_level_pct = 80.0
        self._trig = None
        self._echo = None
        self._init_sensor()

    def _init_sensor(self):
        try:
            self._trig = machine.Pin(self.trig_pin_num, machine.Pin.OUT)
            self._echo = machine.Pin(self.echo_pin_num, machine.Pin.IN)
            self._trig.value(0)
        except Exception:
            self._trig = None
            self._echo = None

    def read_distance_cm(self):
        """
        Measures distance using HC-SR04 pulse timing.
        """
        if self._trig is None or self._echo is None:
            # Under simulation return distance corresponding to ~80% tank fill
            water_depth = (self.last_level_pct / 100.0) * self.max_height_cm
            distance = (self.max_height_cm + self.sensor_offset_cm) - water_depth
            return distance

        try:
            # Trigger 10us pulse
            self._trig.value(0)
            time.sleep_us(2)
            self._trig.value(1)
            time.sleep_us(10)
            self._trig.value(0)

            # Wait for Echo HIGH
            timeout = 30000 # 30ms timeout
            start_t = time.ticks_us()
            while self._echo.value() == 0:
                if time.ticks_diff(time.ticks_us(), start_t) > timeout:
                    return self.max_height_cm
            
            pulse_start = time.ticks_us()
            while self._echo.value() == 1:
                if time.ticks_diff(time.ticks_us(), pulse_start) > timeout:
                    return self.max_height_cm
            pulse_end = time.ticks_us()

            duration = time.ticks_diff(pulse_end, pulse_start)
            # Speed of sound = 343 m/s -> 0.0343 cm/us (divide by 2 for round trip)
            distance = (duration * 0.0343) / 2.0
            return distance
        except Exception:
            return self.max_height_cm

    def read_level_percentage(self):
        """
        Computes water tank fill percentage based on measured distance.
        """
        dist = self.read_distance_cm()
        # Effective water height in tank = (max_height + offset) - dist
        effective_height = (self.max_height_cm + self.sensor_offset_cm) - dist
        pct = (effective_height / float(self.max_height_cm)) * 100.0
        pct = max(0.0, min(100.0, pct))
        self.last_level_pct = round(pct, 1)
        return self.last_level_pct
