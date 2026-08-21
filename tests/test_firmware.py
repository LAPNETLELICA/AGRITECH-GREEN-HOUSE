"""
Automated Pytest Test Suite for ESP32 Modbus RS485 Gateway Firmware and Rules.
"""
import os
import sys
import unittest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
MOCK_DIR = os.path.join(PROJECT_ROOT, "sim", "micropython_mock")

if MOCK_DIR not in sys.path:
    sys.path.insert(0, MOCK_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(1, PROJECT_ROOT)

from firmware import config
from firmware.drivers.desun_uniwill import DesunUniwillSensor, calc_crc16
from firmware.drivers.louvered_box import LouveredBoxSensor
from firmware.drivers.greenhouse_sensor import GreenhouseOutdoorSensor
from firmware.drivers.hydrostatic_sensor import HydrostaticSensor
from firmware.drivers.waveshare_relay import WaveshareRelayBox
from firmware.controllers.climate_controller import ClimateController


class TestModbusGatewayFirmware(unittest.TestCase):

    def setUp(self):
        self.relays = WaveshareRelayBox()
        self.controller = ClimateController(relay_box=self.relays)

    def test_modbus_crc16(self):
        frame = bytes([0x01, 0x03, 0x00, 0x00, 0x00, 0x04])
        crc = calc_crc16(frame)
        self.assertIsInstance(crc, int)

    def test_desun_uniwill_driver(self):
        sensor = DesunUniwillSensor()
        self.assertEqual(sensor.validate_reading("ph", 7.2), "ok")
        self.assertEqual(sensor.validate_reading("ph", 18.0), "out_of_range")
        self.assertEqual(sensor.validate_reading("tds", 450.0), "ok")

    def test_louvered_box_driver(self):
        sensor = LouveredBoxSensor()
        readings = sensor.read_all()
        self.assertIn("indoor_temp", readings)
        self.assertIn("humidity", readings)
        self.assertIn("pressure", readings)
        self.assertIn("light", readings)

    def test_hydrostatic_sensor(self):
        sensor = HydrostaticSensor()
        readings = sensor.read()
        self.assertIn("reservoir_height", readings)
        self.assertEqual(readings["reservoir_height"]["sensor_type"], "reservoir_height")

    def test_waveshare_relay_driver(self):
        res = self.relays.set_actuator("pump", True, source="manual")
        self.assertTrue(self.relays.get_state("pump"))
        self.assertEqual(res["source"], "manual")

        self.relays.set_actuator("pump", False)
        self.assertFalse(self.relays.get_state("pump"))

    def test_rm1_fan_hysteresis_rule(self):
        # Temp >= 30°C turns fan ON
        readings = {"indoor_temp": {"value": 31.0}, "reservoir_height": {"value": 50.0}}
        res = self.controller.evaluate(readings)
        self.assertTrue(self.relays.get_state("fan"))

        # Temp drop to 29°C stays ON (hysteresis band)
        readings = {"indoor_temp": {"value": 29.0}, "reservoir_height": {"value": 50.0}}
        self.controller.evaluate(readings)
        self.assertTrue(self.relays.get_state("fan"))

        # Temp drop to <= 28°C turns fan OFF
        readings = {"indoor_temp": {"value": 27.5}, "reservoir_height": {"value": 50.0}}
        self.controller.evaluate(readings)
        self.assertFalse(self.relays.get_state("fan"))

    def test_rm7_overflow_protection_failsafe(self):
        # Height >= 95cm triggers overflow protection and locks pump OFF
        readings = {"indoor_temp": {"value": 24.0}, "reservoir_height": {"value": 96.0}}
        res = self.controller.evaluate(readings)
        self.assertFalse(self.relays.get_state("pump"))
        self.assertTrue(self.controller.overflow_failsafe_active)

        # Manual attempt to start pump during RM-7 is rejected
        cmd_res = self.controller.handle_manual_command({"actuator_type": "pump", "value": "ON"})
        self.assertEqual(cmd_res["status"], "rejected")
        self.assertFalse(self.relays.get_state("pump"))

if __name__ == "__main__":
    unittest.main()
