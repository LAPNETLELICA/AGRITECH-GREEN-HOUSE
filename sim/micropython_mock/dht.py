"""
MicroPython 'dht' module mock for desktop CPython simulation.
"""

class _DHTBase:
    _simulated_temp = 23.5
    _simulated_humidity = 55.0

    def __init__(self, pin):
        self.pin = pin

    def measure(self):
        pass

    def temperature(self):
        return _DHTBase._simulated_temp

    def humidity(self):
        return _DHTBase._simulated_humidity

    @classmethod
    def set_mock_values(cls, temp_c, humidity_pct):
        cls._simulated_temp = float(temp_c)
        cls._simulated_humidity = float(humidity_pct)

class DHT11(_DHTBase):
    pass

class DHT22(_DHTBase):
    pass
