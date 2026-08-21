"""
Automated Pytest Test Suite for Person A MicroPython Firmware and Simulation.
"""
import os
import sys
import unittest

# Ensure simulation mocks and project root are in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
MOCK_DIR = os.path.join(PROJECT_ROOT, "sim", "micropython_mock")

if MOCK_DIR not in sys.path:
    sys.path.insert(0, MOCK_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(1, PROJECT_ROOT)

from firmware import config
from firmware.drivers.relay import Relay
from firmware.drivers.servo import ServoMotor
from firmware.drivers.soil_sensor import SoilMoistureSensor
from firmware.drivers.dht_sensor import DHTSensor
from firmware.drivers.ultrasonic import UltrasonicSensor
from firmware.controllers.climate_controller import ClimateController
from sim.sensor_simulator import EnvironmentSimulator
import machine

class TestPersonAFirmware(unittest.TestCase):

    def setUp(self):
        self.pump = Relay(26, name="Pump")
        self.fan = Relay(27, name="Fan")
        self.heater = Relay(25, name="Heater")
        self.servo = ServoMotor(14, name="VentServo")
        self.controller = ClimateController(self.pump, self.fan, self.heater, self.servo)

    def test_relay_driver(self):
        self.pump.turn_off()
        self.assertFalse(self.pump.is_on())
        self.assertEqual(self.pump.status_str(), "OFF")

        self.pump.turn_on()
        self.assertTrue(self.pump.is_on())
        self.assertEqual(self.pump.status_str(), "ON")

    def test_servo_driver(self):
        self.servo.set_angle(45)
        self.assertEqual(self.servo.get_angle(), 45)

        # Test out of bounds clamp
        self.servo.set_angle(200)
        self.assertEqual(self.servo.get_angle(), 180)

        self.servo.set_angle(-10)
        self.assertEqual(self.servo.get_angle(), 0)

    def test_soil_moisture_calibration(self):
        sensor = SoilMoistureSensor(34, dry_val=3200, wet_val=1200)

        # Test Dry state
        machine.ADC.set_mock_value(34, 3200)
        self.assertAlmostEqual(sensor.read_percentage(), 0.0, delta=1.0)

        # Test Wet state
        machine.ADC.set_mock_value(34, 1200)
        self.assertAlmostEqual(sensor.read_percentage(), 100.0, delta=1.0)

        # Test Mid-moisture
        machine.ADC.set_mock_value(34, 2200)
        self.assertAlmostEqual(sensor.read_percentage(), 50.0, delta=2.0)

    def test_auto_irrigation_trigger(self):
        telemetry = {
            "temperature": 23.0,
            "humidity": 50.0,
            "soil_moisture": 25.0, # Below 35% threshold
            "water_level": 80.0
        }
        res = self.controller.evaluate(telemetry)
        self.assertEqual(res["pump"], "ON")
        self.assertTrue(self.pump.is_on())

    def test_low_water_safety_lock(self):
        telemetry = {
            "temperature": 23.0,
            "humidity": 50.0,
            "soil_moisture": 20.0, # Dry soil
            "water_level": 5.0    # Below 15% safety limit
        }
        res = self.controller.evaluate(telemetry)
        # Pump must remain OFF due to water safety trip
        self.assertEqual(res["pump"], "OFF")
        self.assertFalse(self.pump.is_on())
        self.assertTrue(any("LOW_WATER" in alert for alert in res["alerts"]))

    def test_auto_cooling_fan_and_vent(self):
        telemetry = {
            "temperature": 32.0, # Hot (> 28°C)
            "humidity": 60.0,
            "soil_moisture": 50.0,
            "water_level": 80.0
        }
        res = self.controller.evaluate(telemetry)
        self.assertEqual(res["fan"], "ON")
        self.assertEqual(res["vent_angle"], 90)
        self.assertEqual(res["heater"], "OFF")

    def test_auto_heating_trigger(self):
        telemetry = {
            "temperature": 12.0, # Cold (< 18°C)
            "humidity": 50.0,
            "soil_moisture": 50.0,
            "water_level": 80.0
        }
        res = self.controller.evaluate(telemetry)
        self.assertEqual(res["heater"], "ON")
        self.assertEqual(res["fan"], "OFF")
        self.assertEqual(res["vent_angle"], 0)

    def test_manual_mqtt_command_handler(self):
        # Override to Manual mode and turn fan ON
        self.controller.handle_manual_command({"action": "SET_MODE", "value": "MANUAL"})
        self.assertEqual(self.controller.mode, "MANUAL")

        self.controller.handle_manual_command({"action": "FAN", "value": "ON"})
        self.assertTrue(self.fan.is_on())

        self.controller.handle_manual_command({"action": "VENT", "value": 60})
        self.assertEqual(self.servo.get_angle(), 60)

    def test_environment_simulator_physics(self):
        sim = EnvironmentSimulator()
        sim.override_soil_moisture(30.0)

        # Update environment with pump ON
        sim.update(dt_sec=2.0, pump_on=True)
        # Soil moisture should increase
        self.assertGreater(sim.soil_moisture_pct, 30.0)

    def test_desun_uniwill_driver(self):
        from firmware.drivers.desun_uniwill import DesunUniwillSensor, calc_crc16
        sensor = DesunUniwillSensor(slave_addr=1)

        # Test Modbus CRC16 calculation
        test_frame = bytes([0x01, 0x03, 0x00, 0x00, 0x00, 0x04])
        crc = calc_crc16(test_frame)
        self.assertIsInstance(crc, int)

        # Test range validation
        self.assertEqual(sensor.validate_reading("ph", 7.2), "ok")
        self.assertEqual(sensor.validate_reading("ph", 18.0), "out_of_range")
        self.assertEqual(sensor.validate_reading("tds", 500.0), "ok")
        self.assertEqual(sensor.validate_reading("tds", 4500.0), "out_of_range")
        self.assertEqual(sensor.validate_reading("ec", 1200.0), "ok")
        self.assertEqual(sensor.validate_reading("water_temp", 24.5), "ok")
        self.assertEqual(sensor.validate_reading("water_temp", -10.0), "out_of_range")

        # Test read_all with stale fallback
        readings = sensor.read_all(mock_fail=True)
        self.assertIn("ph", readings)
        self.assertEqual(readings["ph"]["quality_flag"], "stale")

        # Test read_all with out_of_range mock
        oor_readings = sensor.read_all(mock_fail=True, mock_out_of_range=True)
        self.assertEqual(oor_readings["ph"]["quality_flag"], "out_of_range")

if __name__ == "__main__":
    unittest.main()
