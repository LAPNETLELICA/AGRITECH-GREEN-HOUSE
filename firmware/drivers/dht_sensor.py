"""
DHT11 / DHT22 Temperature & Humidity Sensor Driver.
"""
try:
    import machine
    import dht
except ImportError:
    pass

class DHTSensor:
    def __init__(self, pin_num, sensor_type="DHT22"):
        self.pin_num = pin_num
        self.sensor_type = sensor_type
        self.last_temp = 22.0
        self.last_humidity = 50.0
        self._sensor = None
        self._init_sensor()

    def _init_sensor(self):
        try:
            pin = machine.Pin(self.pin_num, machine.Pin.IN)
            if self.sensor_type.upper() == "DHT11":
                self._sensor = dht.DHT11(pin)
            else:
                self._sensor = dht.DHT22(pin)
        except Exception as e:
            # Under simulation or hardware error, handled gracefully
            self._sensor = None

    def read(self):
        """
        Triggers sensor measurement and returns (temperature_c, humidity_pct).
        Returns previous valid readings on error to maintain stability.
        """
        if self._sensor is not None:
            try:
                self._sensor.measure()
                self.last_temp = float(self._sensor.temperature())
                self.last_humidity = float(self._sensor.humidity())
            except Exception as e:
                pass
        return self.last_temp, self.last_humidity
