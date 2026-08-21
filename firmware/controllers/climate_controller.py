"""
Microclimate Automation State Machine & Threshold Controller for Person A.
"""
import time
from firmware import config
from firmware.utils.logger import Logger

logger = Logger("CLIMATE_CTRL")

class ClimateController:
    MODE_AUTO = "AUTO"
    MODE_MANUAL = "MANUAL"

    def __init__(self, pump_relay, fan_relay, heater_relay, vent_servo):
        self.pump = pump_relay
        self.fan = fan_relay
        self.heater = heater_relay
        self.servo = vent_servo

        self.mode = self.MODE_AUTO
        self.last_pump_start_time = None
        self.alerts = []

    def set_mode(self, mode):
        if mode.upper() in [self.MODE_AUTO, self.MODE_MANUAL]:
            self.mode = mode.upper()
            logger.info("Operating mode changed to: %s", self.mode)
            return True
        return False

    def evaluate(self, telemetry_data):
        """
        Evaluates microclimate state and updates actuators based on current telemetry.
        telemetry_data dict keys: 'temperature', 'humidity', 'soil_moisture', 'water_level', 'light_pct'
        """
        temp = telemetry_data.get("temperature", 22.0)
        humidity = telemetry_data.get("humidity", 50.0)
        soil = telemetry_data.get("soil_moisture", 50.0)
        water = telemetry_data.get("water_level", 80.0)

        self.alerts.clear()

        # Water level safety check (Applies in BOTH Auto and Manual modes)
        if water < config.WATER_TANK_MIN_PCT:
            self.alerts.append("LOW_WATER_WARNING: Water tank level below minimum threshold!")
            if self.pump.is_on():
                logger.warn("Safety Trip! Turning OFF irrigation pump due to low water tank level (%.1f%%)", water)
                self.pump.turn_off()

        # Execute Auto Mode Logic
        if self.mode == self.MODE_AUTO:
            self._process_auto_irrigation(soil, water)
            self._process_auto_climate(temp, humidity)

        return {
            "mode": self.mode,
            "pump": self.pump.status_str(),
            "fan": self.fan.status_str(),
            "heater": self.heater.status_str(),
            "vent_angle": self.servo.get_angle(),
            "alerts": list(self.alerts)
        }

    def _process_auto_irrigation(self, soil, water):
        now = time.time() if hasattr(time, "time") else 0

        # Safety cutoff check for pump runtime limit
        if self.pump.is_on() and self.last_pump_start_time is not None:
            elapsed = now - self.last_pump_start_time
            if elapsed > config.MAX_PUMP_RUN_TIME_SEC:
                logger.warn("Max irrigation pump runtime exceeded (%ds). Turning pump OFF.", elapsed)
                self.pump.turn_off()
                self.last_pump_start_time = None
                return

        # Check if irrigation is needed
        if soil < config.SOIL_MOISTURE_MIN_PCT:
            if water >= config.WATER_TANK_MIN_PCT:
                if not self.pump.is_on():
                    logger.info("Soil dry (%.1f%% < %.1f%%). Starting irrigation pump.", soil, config.SOIL_MOISTURE_MIN_PCT)
                    self.pump.turn_on()
                    self.last_pump_start_time = now
            else:
                self.alerts.append("IRRIGATION_BLOCKED: Tank empty!")

        # Stop irrigation when target humidity reached
        elif soil >= config.SOIL_MOISTURE_TARGET_PCT:
            if self.pump.is_on():
                logger.info("Soil target moisture reached (%.1f%%). Turning OFF pump.", soil)
                self.pump.turn_off()
                self.last_pump_start_time = None

    def _process_auto_climate(self, temp, humidity):
        # High temperature or excessive humidity -> Cooling & Ventilation
        if temp > config.TEMP_MAX_C or humidity > config.HUMIDITY_MAX_PCT:
            if not self.fan.is_on():
                logger.info("High Temp/Humidity detected (%.1f°C / %.1f%%). Turning ON cooling fan.", temp, humidity)
                self.fan.turn_on()
            if self.heater.is_on():
                self.heater.turn_off()
            if self.servo.get_angle() < 90:
                logger.info("Opening roof ventilation hatch to 90°.")
                self.servo.set_angle(90)

        # Low temperature -> Heating & Insulation
        elif temp < config.TEMP_MIN_C:
            if not self.heater.is_on():
                logger.info("Low Temp detected (%.1f°C < %.1f°C). Turning ON heating mat.", temp, config.TEMP_MIN_C)
                self.heater.turn_on()
            if self.fan.is_on():
                self.fan.turn_off()
            if self.servo.get_angle() > 0:
                logger.info("Closing roof ventilation hatch to 0°.")
                self.servo.set_angle(0)

        # Normal climate -> Standby
        else:
            if self.fan.is_on():
                logger.info("Climate normalized. Turning OFF fan.")
                self.fan.turn_off()
            if self.heater.is_on():
                logger.info("Climate normalized. Turning OFF heater.")
                self.heater.turn_off()
            if self.servo.get_angle() > 0:
                self.servo.set_angle(0)

    def handle_manual_command(self, cmd_dict):
        """
        Handles incoming command dicts (e.g. from MQTT).
        Example: {'action': 'SET_MODE', 'value': 'MANUAL'}
                 {'action': 'PUMP', 'value': 'ON'}
                 {'action': 'FAN', 'value': 'OFF'}
                 {'action': 'VENT', 'value': 45}
        """
        action = cmd_dict.get("action", "").upper()
        value = str(cmd_dict.get("value", "")).upper()

        logger.info("Received manual command: %s = %s", action, value)

        if action == "SET_MODE":
            return self.set_mode(value)

        # Switch to manual mode automatically if manual override command sent
        self.mode = self.MODE_MANUAL

        if action == "PUMP":
            if value == "ON":
                self.pump.turn_on()
            else:
                self.pump.turn_off()
        elif action == "FAN":
            if value == "ON":
                self.fan.turn_on()
            else:
                self.fan.turn_off()
        elif action == "HEATER":
            if value == "ON":
                self.heater.turn_on()
            else:
                self.heater.turn_off()
        elif action == "VENT":
            try:
                angle = int(cmd_dict.get("value", 0))
                self.servo.set_angle(angle)
            except ValueError:
                pass
        return True
