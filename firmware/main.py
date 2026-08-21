"""
Main ESP32 Modbus Gateway Application Entry Point - AGRITECH GREENHOUSE.
Coordinates Modbus RS485 cyclic polling (5-10s), rules evaluation (RM-1, RM-2, RM-7), and telemetry broadcast.
"""
import time

from firmware import config
from firmware.utils.logger import Logger
from firmware.drivers.desun_uniwill import DesunUniwillSensor
from firmware.drivers.louvered_box import LouveredBoxSensor
from firmware.drivers.greenhouse_sensor import GreenhouseOutdoorSensor
from firmware.drivers.hydrostatic_sensor import HydrostaticSensor
from firmware.drivers.waveshare_relay import WaveshareRelayBox

from firmware.controllers.climate_controller import ClimateController
from firmware.services.network import NetworkManager
from firmware.services.mqtt_service import MQTTService
from firmware.services.telemetry_service import TelemetryService

logger = Logger("MAIN")


class GreenhouseGatewayApp:
    def __init__(self):
        logger.info("Initializing ESP32 Modbus RS485 Gateway components...")

        # 1. Initialize Modbus RTU Slave Drivers
        self.desun = DesunUniwillSensor()
        self.louvered = LouveredBoxSensor()
        self.outdoor = GreenhouseOutdoorSensor()
        self.hydrostatic = HydrostaticSensor()
        self.relays = WaveshareRelayBox()

        # 2. Initialize Rules & State Machine Controller
        self.controller = ClimateController(relay_box=self.relays)

        # 3. Network & Telemetry Services
        self.net = NetworkManager()
        self.mqtt = MQTTService(command_callback=self.controller.handle_manual_command)
        self.telemetry = TelemetryService()

    def setup(self):
        logger.info("Starting setup procedures...")
        self.net.connect()
        self.mqtt.connect()
        logger.info("Setup complete. ESP32 Gateway ready.")

    def poll_modbus_sensors(self) -> dict:
        """
        Interrogates all 4 Modbus RTU slave devices cyclically (5-10s cycle).
        Returns consolidated sensor readings dictionary with quality_flags.
        """
        readings = {}
        readings.update(self.desun.read_all())
        readings.update(self.louvered.read_all())
        readings.update(self.outdoor.read())
        readings.update(self.hydrostatic.read())
        return readings

    def run_cycle(self):
        """
        Executes one cyclic iteration of Modbus polling, rules evaluation, and telemetry.
        """
        # 1. Interrogate Modbus RTU sensors cyclically (5-10s)
        sensor_readings = {}
        sensor_readings.update(self.desun.read_all())
        sensor_readings.update(self.louvered.read_all())
        sensor_readings.update(self.outdoor.read())
        sensor_readings.update(self.hydrostatic.read())

        # 2. Evaluate Automation Rules & Failsafes (RM-1, RM-2, RM-7)
        ctrl_status = self.controller.evaluate(sensor_readings)

        # 3. Prepare Batch Telemetry Payload (Flux 1 Specification)
        batch_payload = []
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ") if hasattr(time, "strftime") else "2026-08-01T09:12:04Z"
        for stype, item in sensor_readings.items():
            batch_payload.append({
                "device_id": config.DEVICE_ID,
                "sensor_type": stype,
                "value": item["value"],
                "quality_flag": item["quality_flag"],
                "recorded_at": now_iso
            })

        # 4. Transmit Batch to Backend & MQTT
        self.telemetry.publish_batch(batch_payload)
        self.mqtt.check_messages()

        # 5. Handle Alerts (Flux 4)
        for alert in ctrl_status.get("alerts", []):
            self.telemetry.publish_alert(alert)
            self.mqtt.publish_alert(alert)

        return {
            "device_id": config.DEVICE_ID,
            "readings": sensor_readings,
            "actuators": ctrl_status["actuators"],
            "mode": ctrl_status["mode"],
            "alerts": ctrl_status["alerts"]
        }

    def start_loop(self, max_cycles=None):
        self.setup()
        cycles = 0
        logger.info("Entering main control loop (Polling cycle: %.1fs)...", config.POLLING_CYCLE_SEC)
        try:
            while True:
                self.run_cycle()
                cycles += 1
                if max_cycles and cycles >= max_cycles:
                    logger.info("Reached maximum requested loop cycles (%d). Stopping.", max_cycles)
                    break
                time.sleep(config.POLLING_CYCLE_SEC)
        except KeyboardInterrupt:
            logger.info("Loop interrupted by user.")

if __name__ == "__main__":
    app = GreenhouseGatewayApp()
    app.start_loop()
