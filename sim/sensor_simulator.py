"""
Dynamic Greenhouse Physical Environment Simulator.
Simulates environmental physics (diurnal cycles, soil drying, irrigation, ventilation, heating, tank depletion).
"""
import math
import time
import machine
import dht
from firmware import config

class EnvironmentSimulator:
    def __init__(self):
        self.sim_time_sec = 0.0
        self.base_temp_c = 22.0
        self.temp_c = 23.5
        self.humidity_pct = 55.0
        self.soil_moisture_pct = 40.0
        self.light_pct = 70.0
        self.water_level_pct = 85.0

        # Environmental physics state flags
        self.rain_active = False

    def update(self, dt_sec, pump_on=False, fan_on=False, heater_on=False, vent_angle=0):
        """
        Updates environmental variables over time step dt_sec (in seconds).
        """
        self.sim_time_sec += dt_sec

        # 1. Diurnal cycle (Temperature & Light)
        # 1 full day cycle = 240 seconds in simulation time (10 seconds = 1 hour)
        day_progress = (self.sim_time_sec % 240.0) / 240.0
        day_rad = day_progress * 2.0 * math.pi

        # Solar light intensity (peaks at midday ~ 0.5 day_progress)
        sun_factor = max(0.0, math.sin(day_rad - math.pi / 2))
        self.light_pct = round(10.0 + sun_factor * 85.0, 1)

        # Ambient natural temperature variation (+/- 6 degrees C)
        target_ambient_temp = self.base_temp_c + sun_factor * 8.0 - 2.0

        # 2. Apply Heating / Cooling Actuator Dynamics
        if heater_on:
            self.temp_c += 0.8 * dt_sec # Heating mat adds heat
        if fan_on or vent_angle >= 45:
            # Fan or open roof cools down toward outside ambient
            cooling_rate = 0.6 * dt_sec
            if self.temp_c > target_ambient_temp:
                self.temp_c = max(target_ambient_temp, self.temp_c - cooling_rate)
            self.humidity_pct = max(30.0, self.humidity_pct - 0.5 * dt_sec)
        else:
            # Heat moves towards natural ambient
            self.temp_c += (target_ambient_temp - self.temp_c) * 0.05 * dt_sec

        self.temp_c = round(self.temp_c, 1)

        # 3. Apply Irrigation & Soil Moisture Dynamics
        if pump_on and self.water_level_pct > 0:
            # Pump adds moisture to soil
            self.soil_moisture_pct = min(100.0, self.soil_moisture_pct + 3.0 * dt_sec)
            # Pump consumes water from tank
            self.water_level_pct = max(0.0, self.water_level_pct - 1.2 * dt_sec)
        else:
            # Evapotranspiration slowly dries soil
            drying_rate = 0.15 * dt_sec * (1.0 + self.temp_c / 30.0)
            self.soil_moisture_pct = max(10.0, self.soil_moisture_pct - drying_rate)

        if self.rain_active:
            self.water_level_pct = min(100.0, self.water_level_pct + 2.0 * dt_sec)

        self.soil_moisture_pct = round(self.soil_moisture_pct, 1)
        self.water_level_pct = round(self.water_level_pct, 1)

        # 4. Sync values to MicroPython Hardware Mocks
        self._sync_to_hardware_mocks()

    def _sync_to_hardware_mocks(self):
        # Update DHT mock values
        dht.DHT22.set_mock_values(self.temp_c, self.humidity_pct)

        # Update Soil Moisture ADC mock value
        # Invert percentage back to ADC raw (3200 dry -> 1200 wet)
        soil_adc = config.SOIL_ADC_DRY - (self.soil_moisture_pct / 100.0) * (config.SOIL_ADC_DRY - config.SOIL_ADC_WET)
        machine.ADC.set_mock_value(config.SOIL_ADC_PIN, soil_adc)

        # Update Light ADC mock value
        light_adc = config.LIGHT_ADC_DARK - (self.light_pct / 100.0) * (config.LIGHT_ADC_DARK - config.LIGHT_ADC_BRIGHT)
        machine.ADC.set_mock_value(config.LIGHT_ADC_PIN, light_adc)

    # Manual Overrides for testing
    def override_soil_moisture(self, pct):
        self.soil_moisture_pct = max(0.0, min(100.0, float(pct)))
        self._sync_to_hardware_mocks()

    def override_temperature(self, temp_c):
        self.temp_c = float(temp_c)
        self._sync_to_hardware_mocks()

    def override_water_level(self, pct):
        self.water_level_pct = max(0.0, min(100.0, float(pct)))

    def toggle_rain(self):
        self.rain_active = not self.rain_active
        return self.rain_active
