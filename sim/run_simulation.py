#!/usr/bin/env python3
"""
Interactive CLI Runner & Dashboard for Person A MicroPython Local Simulation.
Runs the MicroPython firmware in a simulated physical environment on PC.
"""
import os
import sys
import time
import threading

# Add workspace root and micropython_mock directory to sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
MOCK_DIR = os.path.join(SCRIPT_DIR, "micropython_mock")

if MOCK_DIR not in sys.path:
    sys.path.insert(0, MOCK_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(1, PROJECT_ROOT)

from sim.sensor_simulator import EnvironmentSimulator
from sim.mqtt_broker_mock import get_mock_mqtt_broker
from firmware.main import PersonANodeApp

class SimulationRunner:
    def __init__(self, step_delay=1.0):
        self.step_delay = step_delay
        self.env = EnvironmentSimulator()
        self.app = PersonANodeApp()
        self.broker = get_mock_mqtt_broker()
        self.running = False
        self.cycle_count = 0
        self.last_telemetry = {}

    def start(self):
        self.app.setup()
        self.running = True
        print("\033[2J\033[H", end="") # Clear terminal screen

        # Main Loop
        try:
            while self.running:
                self.step()
                self.render_dashboard()
                time.sleep(self.step_delay)
        except KeyboardInterrupt:
            self.stop()

    def step(self):
        self.cycle_count += 1

        # 1. Get current actuator states
        pump_on = self.app.pump_relay.is_on()
        fan_on = self.app.fan_relay.is_on()
        heater_on = self.app.heater_relay.is_on()
        vent_angle = self.app.vent_servo.get_angle()

        # 2. Update physical environment simulator
        self.env.update(
            dt_sec=self.step_delay,
            pump_on=pump_on,
            fan_on=fan_on,
            heater_on=heater_on,
            vent_angle=vent_angle
        )

        # 3. Execute one firmware cycle
        self.last_telemetry = self.app.run_cycle()

    def render_dashboard(self):
        # Move cursor to top left
        print("\033[H", end="")

        t = self.last_telemetry
        acts = t.get("actuators", {})
        mode = t.get("mode", "AUTO")
        alerts = t.get("alerts", [])

        # Color codes
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        RED = "\033[91m"
        CYAN = "\033[96m"
        BOLD = "\033[1m"
        RESET = "\033[0m"

        def fmt_status(state_str):
            if state_str == "ON" or (isinstance(state_str, int) and state_str > 0):
                return f"{GREEN}{BOLD}[ ON ]{RESET}"
            return f"{RED}[OFF]{RESET}"

        print(f"{CYAN}{BOLD}" + "="*70 + f"{RESET}")
        print(f"{CYAN}{BOLD}  AGRITECH GREENHOUSE - PERSON A LOCAL SIMULATION ENVIRONMENT{RESET}")
        print(f"  Node ID: {t.get('device_id')} | Version: 1.0.0 | Cycle: #{self.cycle_count}")
        print(f"{CYAN}{BOLD}" + "="*70 + f"{RESET}")

        print(f"\n{BOLD}► OPERATING MODE:{RESET} [{GREEN if mode == 'AUTO' else YELLOW}{mode}{RESET}]")

        print(f"\n{BOLD}► SENSOR TELEMETRY (Microclimate & Soil):{RESET}")
        print(f"  • Temperature   : {CYAN}{t.get('temperature', 0):>5.1f} °C{RESET}  (Target: 18.0 - 28.0 °C)")
        print(f"  • Air Humidity  : {CYAN}{t.get('humidity', 0):>5.1f} %{RESET}   (Max: 80.0 %)")
        print(f"  • Soil Moisture : {CYAN}{t.get('soil_moisture', 0):>5.1f} %{RESET}   (Min: 35.0 %, Target: 65.0 %)")
        print(f"  • Water Tank    : {CYAN}{t.get('water_level', 0):>5.1f} %{RESET}   (Safety Cutoff: 15.0 %)")
        print(f"  • Ambient Light : {CYAN}{t.get('light_intensity', 0):>5.1f} %{RESET}")

        print(f"\n{BOLD}► DESUN UNIWILL MODBUS RS485 (Water Quality):{RESET}")
        ph_val = t.get('ph', 7.2)
        tds_val = t.get('tds', 450.0)
        ec_val = t.get('ec', 850.0)
        wtemp_val = t.get('water_temp', 21.0)
        wq = t.get('water_quality', {})
        ph_flag = wq.get('ph', {}).get('quality_flag', 'ok')
        tds_flag = wq.get('tds', {}).get('quality_flag', 'ok')
        ec_flag = wq.get('ec', {}).get('quality_flag', 'ok')
        wtemp_flag = wq.get('water_temp', {}).get('quality_flag', 'ok')

        print(f"  • Water pH      : {CYAN}{ph_val:>5.2f} pH{RESET}   [Flag: {GREEN if ph_flag=='ok' else RED}{ph_flag}{RESET}] (Range: 0 - 14)")
        print(f"  • Water TDS     : {CYAN}{tds_val:>5.1f} ppm{RESET}  [Flag: {GREEN if tds_flag=='ok' else RED}{tds_flag}{RESET}] (Range: 0 - 3000 ppm)")
        print(f"  • Water EC      : {CYAN}{ec_val:>5.1f} uS/cm{RESET} [Flag: {GREEN if ec_flag=='ok' else RED}{ec_flag}{RESET}] (Range: 0 - 5000 uS/cm)")
        print(f"  • Water Temp    : {CYAN}{wtemp_val:>5.1f} °C{RESET}   [Flag: {GREEN if wtemp_flag=='ok' else RED}{wtemp_flag}{RESET}] (Range: 0 - 50 °C)")

        print(f"\n{BOLD}► ACTUATOR STATES:{RESET}")
        print(f"  • Water Pump Relay : {fmt_status(acts.get('pump'))}")
        print(f"  • Cooling Fan Relay: {fmt_status(acts.get('fan'))}")
        print(f"  • Heating Mat Relay: {fmt_status(acts.get('heater'))}")
        print(f"  • Roof Vent Servo  : {acts.get('vent_angle', 0)}° ({'OPEN' if acts.get('vent_angle', 0)>0 else 'CLOSED'})")

        print(f"\n{BOLD}► ACTIVE ALERTS / SAFETY LOCKS:{RESET}")
        if alerts:
            for a in alerts:
                print(f"  {RED}{BOLD}⚠ {a}{RESET}")
        else:
            print(f"  {GREEN}✔ All systems nominal. No safety trips.{RESET}")

        print(f"\n{BOLD}► MQTT BROKER LOG (Last 3 Rx/Tx Messages):{RESET}")
        history = self.broker.get_history()[-3:]
        if history:
            for topic, msg, sender in history:
                print(f"  [{sender}] -> {topic}: {msg[:50]}...")
        else:
            print("  (No messages)")

        print(f"\n{CYAN}" + "-"*70 + f"{RESET}")
        print(f"{BOLD}INTERACTIVE ACTIONS:{RESET}")
        print("  [1] Simulate Dry Soil (<35%)   [2] Simulate Heatwave (>30°C)")
        print("  [3] Simulate Cold Drop (<15°C)  [4] Empty Water Tank (<10%)")
        print("  [5] Refill Water Tank (100%)   [6] Toggle Rain Simulation")
        print("  [m] Send Manual MQTT Command   [q] Exit Simulation")
        print(f"{CYAN}" + "-"*70 + f"{RESET}")

    def inject_action(self, choice):
        choice = choice.strip().lower()
        if choice == '1':
            self.env.override_soil_moisture(20.0)
        elif choice == '2':
            self.env.override_temperature(34.0)
        elif choice == '3':
            self.env.override_temperature(12.0)
        elif choice == '4':
            self.env.override_water_level(5.0)
        elif choice == '5':
            self.env.override_water_level(100.0)
        elif choice == '6':
            rain_st = self.env.toggle_rain()
            print(f"\nRain simulation: {'ACTIVE' if rain_st else 'STOPPED'}")
            time.sleep(1)
        elif choice == 'm':
            print("\nSend Manual MQTT Command:")
            print("Options: PUMP ON | PUMP OFF | FAN ON | FAN OFF | HEATER ON | HEATER OFF | MODE AUTO | MODE MANUAL")
            cmd_str = input("Enter command: ").strip().upper()
            if cmd_str:
                parts = cmd_str.split()
                if len(parts) == 2:
                    action, val = parts[0], parts[1]
                    if action == "MODE":
                        cmd_payload = '{"action": "SET_MODE", "value": "%s"}' % val
                    else:
                        cmd_payload = '{"action": "%s", "value": "%s"}' % (action, val)
                    self.broker.publish("greenhouse/person_a/commands", cmd_payload, sender_id="USER_CONSOLE")
                    time.sleep(1)
        elif choice == 'q':
            self.running = False

    def stop(self):
        self.running = False
        print(f"\nSimulation stopped. Exiting.")

if __name__ == "__main__":
    runner = SimulationRunner(step_delay=1.5)

    # Interactive input thread
    def input_thread():
        while runner.running:
            try:
                ch = input()
                if ch:
                    runner.inject_action(ch)
            except (EOFError, KeyboardInterrupt):
                break

    t_in = threading.Thread(target=input_thread, daemon=True)
    t_in.start()

    runner.start()
