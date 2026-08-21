#!/usr/bin/env python3
"""
Interactive CLI Runner & Dashboard for ESP32 Modbus Gateway Simulation.
"""
import os
import sys
import time
import threading

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
MOCK_DIR = os.path.join(SCRIPT_DIR, "micropython_mock")

if MOCK_DIR not in sys.path:
    sys.path.insert(0, MOCK_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(1, PROJECT_ROOT)

from sim.sensor_simulator import EnvironmentSimulator
from sim.mqtt_broker_mock import get_mock_mqtt_broker
from firmware.main import GreenhouseGatewayApp


class SimulationRunner:
    def __init__(self, step_delay=1.0):
        self.step_delay = step_delay
        self.env = EnvironmentSimulator()
        self.app = GreenhouseGatewayApp()
        self.broker = get_mock_mqtt_broker()
        self.running = False
        self.cycle_count = 0
        self.last_telemetry = {}

    def start(self):
        self.app.setup()
        self.running = True
        print("\033[2J\033[H", end="")

        try:
            while self.running:
                self.step()
                self.render_dashboard()
                time.sleep(self.step_delay)
        except KeyboardInterrupt:
            self.stop()

    def step(self):
        self.cycle_count += 1
        pump_on = self.app.relays.get_state("pump")
        fan_on = self.app.relays.get_state("fan")

        self.env.update(dt_sec=self.step_delay, pump_on=pump_on, fan_on=fan_on)
        self.last_telemetry = self.app.run_cycle()

    def render_dashboard(self):
        print("\033[H", end="")
        t = self.last_telemetry
        readings = t.get("readings", {})
        acts = t.get("actuators", {})
        mode = t.get("mode", "AUTO")
        alerts = t.get("alerts", [])

        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        RED = "\033[91m"
        CYAN = "\033[96m"
        BOLD = "\033[1m"
        RESET = "\033[0m"

        def fmt_flag(flag):
            if flag == "ok":
                return f"{GREEN}[ok]{RESET}"
            elif flag == "stale":
                return f"{YELLOW}[stale]{RESET}"
            return f"{RED}[out_of_range]{RESET}"

        def fmt_act(st):
            return f"{GREEN}{BOLD}[ ON ]{RESET}" if st else f"{RED}[OFF]{RESET}"

        print(f"{CYAN}{BOLD}" + "="*75 + f"{RESET}")
        print(f"{CYAN}{BOLD}  AGRITECH GREENHOUSE - ESP32 MODBUS RS485 GATEWAY SIMULATOR{RESET}")
        print(f"  Device: {t.get('device_id')} | Version: 2.0.0 | Cycle: #{self.cycle_count}")
        print(f"{CYAN}{BOLD}" + "="*75 + f"{RESET}")

        print(f"\n{BOLD}► OPERATING MODE:{RESET} [{GREEN if mode == 'AUTO' else YELLOW}{mode}{RESET}]")

        print(f"\n{BOLD}► DESUN UNIWILL (Water Quality):{RESET}")
        ph = readings.get("ph", {})
        tds = readings.get("tds", {})
        ec = readings.get("ec", {})
        wtemp = readings.get("water_temp", {})
        print(f"  • Water pH     : {CYAN}{ph.get('value', 7.2):>5.2f} pH{RESET}    {fmt_flag(ph.get('quality_flag', 'ok'))}")
        print(f"  • Water TDS    : {CYAN}{tds.get('value', 450.0):>5.1f} ppm{RESET}   {fmt_flag(tds.get('quality_flag', 'ok'))}")
        print(f"  • Water EC     : {CYAN}{ec.get('value', 850.0):>5.1f} uS/cm{RESET} {fmt_flag(ec.get('quality_flag', 'ok'))}")
        print(f"  • Water Temp   : {CYAN}{wtemp.get('value', 21.5):>5.1f} °C{RESET}    {fmt_flag(wtemp.get('quality_flag', 'ok'))}")

        print(f"\n{BOLD}► LOUVERED BOX & OUTDOOR SENSORS (Climate):{RESET}")
        itemp = readings.get("indoor_temp", {})
        hum = readings.get("humidity", {})
        press = readings.get("pressure", {})
        light = readings.get("light", {})
        otemp = readings.get("outdoor_temp", {})
        print(f"  • Indoor Temp  : {CYAN}{itemp.get('value', 24.0):>5.1f} °C{RESET}    {fmt_flag(itemp.get('quality_flag', 'ok'))} (Fan ON >=30°C, OFF <=28°C)")
        print(f"  • Humidity     : {CYAN}{hum.get('value', 55.0):>5.1f} %RH{RESET}   {fmt_flag(hum.get('quality_flag', 'ok'))}")
        print(f"  • Pressure     : {CYAN}{press.get('value', 1013.2):>5.1f} hPa{RESET}  {fmt_flag(press.get('quality_flag', 'ok'))}")
        print(f"  • Light        : {CYAN}{light.get('value', 12500):>7.0f} lux{RESET}  {fmt_flag(light.get('quality_flag', 'ok'))}")
        print(f"  • Outdoor Temp : {CYAN}{otemp.get('value', 19.5):>5.1f} °C{RESET}    {fmt_flag(otemp.get('quality_flag', 'ok'))}")

        print(f"\n{BOLD}► HYDROSTATIC WATER LEVEL SENSOR:{RESET}")
        h = readings.get("reservoir_height", {})
        print(f"  • Reservoir Ht : {CYAN}{h.get('value', 42.7):>5.1f} cm{RESET}    {fmt_flag(h.get('quality_flag', 'ok'))} (Low <=15cm, Crit <=5cm, High >=85cm, Overflow >=95cm)")

        print(f"\n{BOLD}► WAVESHARE 4-CHANNEL RELAY ACTUATORS:{RESET}")
        print(f"  • Pump         : {fmt_act(acts.get('pump'))}")
        print(f"  • Master Valve : {fmt_act(acts.get('master_valve'))}")
        print(f"  • Section Valve: {fmt_act(acts.get('section_valve'))}")
        print(f"  • Fan          : {fmt_act(acts.get('fan'))}")
        print(f"  • LED Light    : {fmt_act(acts.get('led_light'))}")

        print(f"\n{BOLD}► ALERTS & FAILSAFES:{RESET}")
        if alerts:
            for a in alerts:
                print(f"  {RED}{BOLD}⚠ [{a.get('alert_type')}] {a.get('message')}{RESET}")
        else:
            print(f"  {GREEN}✔ Nominal operating condition.{RESET}")

        print(f"\n{CYAN}" + "-"*75 + f"{RESET}")
        print(f"{BOLD}INTERACTIVE SIMULATION ACTIONS:{RESET}")
        print("  [1] Low Water Warning (12cm)     [2] Critical Low Water Auto-Fill (3cm)")
        print("  [3] Overflow Risk (98cm Failsafe) [4] Indoor Heatwave (32°C Fan Trigger)")
        print("  [5] Normal Water Height (50cm)   [m] Send Manual Command")
        print("  [q] Exit Simulation")
        print(f"{CYAN}" + "-"*75 + f"{RESET}")

    def inject_action(self, choice):
        ch = choice.strip().lower()
        if ch == '1':
            self.env.override_reservoir_height(12.0)
        elif ch == '2':
            self.env.override_reservoir_height(3.0)
        elif ch == '3':
            self.env.override_reservoir_height(98.0)
        elif ch == '4':
            self.env.override_indoor_temp(32.0)
        elif ch == '5':
            self.env.override_reservoir_height(50.0)
        elif ch == 'm':
            print("\nManual Command (e.g. pump ON / fan ON / mode MANUAL):")
            cmd = input("Command: ").strip().upper()
            if cmd:
                parts = cmd.split()
                if len(parts) == 2:
                    act, val = parts[0], parts[1]
                    if act == "MODE":
                        self.app.controller.handle_manual_command({"action": "SET_MODE", "value": val})
                    else:
                        self.app.controller.handle_manual_command({"actuator_type": act.lower(), "value": val})
        elif ch == 'q':
            self.running = False

    def stop(self):
        self.running = False

if __name__ == "__main__":
    runner = SimulationRunner(step_delay=1.5)

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
