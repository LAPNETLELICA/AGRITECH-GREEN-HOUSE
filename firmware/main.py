"""
Main Application Entry Point - AGRITECH GREENHOUSE (Person A)
Coordinates sensor reads, climate controller logic, actuator outputs, and MQTT telemetry.
"""
import time

from firmware import config
from firmware.utils.logger import Logger
from firmware.drivers.dht_sensor import DHTSensor
from firmware.drivers.soil_sensor import SoilMoistureSensor
from firmware.drivers.light_sensor import LightSensor
from firmware.drivers.ultrasonic import UltrasonicSensor
from firmware.drivers.relay import Relay
from firmware.drivers.servo import ServoMotor
from firmware.drivers.desun_uniwill import DesunUniwillSensor
from firmware.controllers.climate_controller import ClimateController
from firmware.services.network import NetworkManager
from firmware.services.mqtt_service import MQTTService

logger = Logger("MAIN")

class PersonANodeApp:
    def __init__(self):
        logger.info("Initializing Person A Greenhouse Firmware components...")

        # Initialize Drivers
        self.dht = DHTSensor(config.DHT_PIN, sensor_type="DHT22")
        self.soil = SoilMoistureSensor(config.SOIL_ADC_PIN, config.SOIL_ADC_DRY, config.SOIL_ADC_WET)
        self.light = LightSensor(config.LIGHT_ADC_PIN, config.LIGHT_ADC_DARK, config.LIGHT_ADC_BRIGHT)
        self.ultrasonic = UltrasonicSensor(config.ULTRASONIC_TRIG_PIN, config.ULTRASONIC_ECHO_PIN, config.WATER_TANK_MAX_HEIGHT_CM)
        self.desun = DesunUniwillSensor()

        self.pump_relay = Relay(config.RELAY_PUMP_PIN, name="WaterPump")
        self.fan_relay = Relay(config.RELAY_FAN_PIN, name="CoolingFan")
        self.heater_relay = Relay(config.RELAY_HEATER_PIN, name="HeaterMat")
        self.vent_servo = ServoMotor(config.SERVO_VENT_PIN, name="RoofVentServo")

        # Initialize Controller
        self.controller = ClimateController(
            pump_relay=self.pump_relay,
            fan_relay=self.fan_relay,
            heater_relay=self.heater_relay,
            vent_servo=self.vent_servo
        )

        # Network & Services
        self.net = NetworkManager()
        self.mqtt = MQTTService(command_callback=self.controller.handle_manual_command)

    def setup(self):
        logger.info("Starting setup procedures...")
        self.net.connect()
        self.mqtt.connect()
        logger.info("Setup complete. Node ready.")

    def run_cycle(self):
        """
        Executes one iteration of sensor reading, climate evaluation, and telemetry broadcast.
        Returns the generated telemetry dict.
        """
        # 1. Read Sensors
        temp_c, humidity_pct = self.dht.read()
        soil_pct = self.soil.read_percentage()
        light_pct = self.light.read_percentage()
        water_pct = self.ultrasonic.read_level_percentage()
        water_quality = self.desun.read_all()

        telemetry = {
            "device_id": config.DEVICE_ID,
            "node_type": config.NODE_TYPE,
            "temperature": temp_c,
            "humidity": humidity_pct,
            "soil_moisture": soil_pct,
            "light_intensity": light_pct,
            "water_level": water_pct,
            "water_quality": water_quality,
            "ph": water_quality["ph"]["value"],
            "tds": water_quality["tds"]["value"],
            "ec": water_quality["ec"]["value"],
            "water_temp": water_quality["water_temp"]["value"],
            "timestamp": time.time() if hasattr(time, "time") else 0
        }

        # 2. Evaluate Automation State Machine
        ctrl_status = self.controller.evaluate(telemetry)
        telemetry.update({
            "mode": ctrl_status["mode"],
            "actuators": {
                "pump": ctrl_status["pump"],
                "fan": ctrl_status["fan"],
                "heater": ctrl_status["heater"],
                "vent_angle": ctrl_status["vent_angle"]
            },
            "alerts": ctrl_status["alerts"]
        })

        # 3. Handle MQTT poll & Telemetry publish
        self.mqtt.check_messages()
        self.mqtt.publish_telemetry(telemetry)

        # Check for alerts to publish
        for alert in ctrl_status["alerts"]:
            self.mqtt.publish_alert(alert)

        return telemetry

    def start_loop(self, max_cycles=None):
        self.setup()
        cycles = 0
        logger.info("Entering main control loop...")
        try:
            while True:
                self.run_cycle()
                cycles += 1
                if max_cycles and cycles >= max_cycles:
                    logger.info("Reached maximum requested loop cycles (%d). Stopping.", max_cycles)
                    break
                time.sleep(config.SENSOR_READ_INTERVAL_MS / 1000.0)
        except KeyboardInterrupt:
            logger.info("Loop interrupted by user.")

if __name__ == "__main__":
    app = PersonANodeApp()
    app.start_loop()
