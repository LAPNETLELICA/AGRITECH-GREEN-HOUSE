"""
Greenhouse Physical Environment Simulator (Modbus RTU Digital Twin).
Simulates diurnal solar cycles, temperature, humidity, pressure, light, and reservoir height.
"""
import math
import time
from firmware import config


class EnvironmentSimulator:
    """
    Simulates physical dynamics of the greenhouse for local PC testing.
    """

    def __init__(self):
        self.sim_time_sec = 0.0

        # Desun Uniwill (Water Quality)
        self.ph = 7.2
        self.tds = 450.0
        self.ec = 850.0
        self.water_temp = 21.5

        # Louvered Box (Indoor Climate)
        self.indoor_temp = 24.0
        self.humidity = 55.0
        self.pressure = 1013.25
        self.light = 12500.0

        # Greenhouse Outdoor
        self.outdoor_temp = 19.5

        # Hydrostatic Tank (Reservoir Height in cm)
        self.reservoir_height = 42.7

    def update(self, dt_sec: float, pump_on: bool = False, fan_on: bool = False):
        """
        Updates physical simulation state over dt_sec seconds.
        """
        self.sim_time_sec += dt_sec

        # Diurnal solar cycle
        day_progress = (self.sim_time_sec % 240.0) / 240.0
        day_rad = day_progress * 2.0 * math.pi
        sun_factor = max(0.0, math.sin(day_rad - math.pi / 2))

        # Solar light intensity (0 to 85,000 lux)
        self.light = round(500.0 + sun_factor * 84500.0, 1)

        # Outdoor ambient temperature (-20 to 55 °C)
        self.outdoor_temp = round(15.0 + sun_factor * 10.0, 1)

        # Thermal dynamics
        if fan_on:
            # Fan cools indoor temp towards outdoor temp
            if self.indoor_temp > self.outdoor_temp:
                self.indoor_temp = max(self.outdoor_temp, self.indoor_temp - 0.5 * dt_sec)
        else:
            # Heat builds up in greenhouse
            target_temp = self.outdoor_temp + sun_factor * 8.0
            self.indoor_temp += (target_temp - self.indoor_temp) * 0.05 * dt_sec

        self.indoor_temp = round(self.indoor_temp, 1)

        # Reservoir height dynamics (0 to 100 cm)
        if pump_on:
            # Pump fills or consumes reservoir water
            self.reservoir_height = min(100.0, self.reservoir_height + 1.5 * dt_sec)
        else:
            # Slow evaporation
            self.reservoir_height = max(0.0, self.reservoir_height - 0.02 * dt_sec)

        self.reservoir_height = round(self.reservoir_height, 1)

    # Manual override helpers for interactive CLI simulation testing
    def override_reservoir_height(self, height_cm: float):
        self.reservoir_height = max(0.0, min(100.0, float(height_cm)))

    def override_indoor_temp(self, temp_c: float):
        self.indoor_temp = float(temp_c)
