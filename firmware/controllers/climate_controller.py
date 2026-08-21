"""
Greenhouse Automation & Safety State Machine (Climate & Reservoir Rules RM-1, RM-2, RM-5, RM-7).
"""
import time
from firmware import config
from firmware.utils.logger import Logger

logger = Logger("CLIMATE_CTRL")


class ClimateController:
    """
    State machine implementing RM-1 (Fan Hysteresis), RM-2 (Auto Fill), and RM-7 (Overflow Failsafe).
    """

    def __init__(self, relay_box):
        self.relays = relay_box
        self.mode = "AUTO" # AUTO or MANUAL

        # Low Reservoir Alert & Auto-Fill Tracking State (RM-2)
        self.low_warning_active = False
        self.low_warning_time = None
        self.auto_fill_active = False
        self.auto_fill_start_time = None

        # Overflow Failsafe State (RM-7)
        self.overflow_failsafe_active = False

    def evaluate(self, sensor_readings: dict) -> dict:
        """
        Evaluates sensor readings against business rules (RM-1, RM-2, RM-7) in AUTO mode.
        Returns control results and active alerts.
        """
        now = time.time() if hasattr(time, "time") else 0
        alerts = []

        # Extract sensor readings
        indoor_temp = sensor_readings.get("indoor_temp", {}).get("value", 24.0)
        reservoir_height = sensor_readings.get("reservoir_height", {}).get("value", 45.0)

        # -------------------------------------------------------------
        # 1. RM-7: OVERFLOW PROTECTION FAILSAFE (Highest Priority)
        # -------------------------------------------------------------
        if reservoir_height >= config.RESERVOIR_OVERFLOW_THRESHOLD_CM:
            self.overflow_failsafe_active = True
            # Force pump OFF immediately
            self.relays.set_actuator("pump", False, source="failsafe:RM-7")
            alerts.append({
                "alert_type": "reservoir_overflow_risk",
                "severity": "critical",
                "message": "Niveau critique (>=95cm) — pompe bloquée pour éviter le débordement"
            })
            alerts.append({
                "alert_type": "pump_failsafe",
                "severity": "critical",
                "message": "Protection anti-débordement active (RM-7)"
            })
        elif reservoir_height <= config.RESERVOIR_HIGH_THRESHOLD_CM:
            self.overflow_failsafe_active = False
        elif reservoir_height >= config.RESERVOIR_HIGH_THRESHOLD_CM:
            alerts.append({
                "alert_type": "high_reservoir_warning",
                "severity": "warning",
                "message": "Niveau réservoir haut (>=85cm)"
            })

        # In MANUAL mode, skip automatic rules (unless RM-7 failsafe is active)
        if self.mode == "MANUAL":
            return {
                "mode": self.mode,
                "actuators": self.relays.get_all_states(),
                "alerts": alerts
            }

        # -------------------------------------------------------------
        # 2. RM-1: FAN HYSTERESIS CONTROL (30.0°C ON, 28.0°C OFF)
        # -------------------------------------------------------------
        current_fan = self.relays.get_state("fan")
        if indoor_temp >= config.FAN_TEMP_ON_C:
            if not current_fan:
                logger.info("RM-1: Température élevée (%.1f°C >= 30°C). Démarrage ventilateur.", indoor_temp)
                self.relays.set_actuator("fan", True, source="rule:RM-1")
        elif indoor_temp <= config.FAN_TEMP_OFF_C:
            if current_fan:
                logger.info("RM-1: Température rafraîchie (%.1f°C <= 28°C). Arrêt ventilateur.", indoor_temp)
                self.relays.set_actuator("fan", False, source="rule:RM-1")

        # -------------------------------------------------------------
        # 3. RM-2: RESERVOIR LOW LEVEL WARNING & AUTO-FILL PUMP RULE
        # -------------------------------------------------------------
        if not self.overflow_failsafe_active:
            if reservoir_height <= config.RESERVOIR_LOW_THRESHOLD_CM:
                if not self.low_warning_active:
                    self.low_warning_active = True
                    self.low_warning_time = now
                    alerts.append({
                        "alert_type": "low_reservoir_warning",
                        "severity": "warning",
                        "message": "Niveau bas (<=15cm) — démarrez la pompe manuellement ou elle démarrera automatiquement dans 5 min"
                    })

                # Check if critical threshold (5cm) reached and response timeout elapsed
                elapsed_warning = (now - self.low_warning_time) if self.low_warning_time else 0
                if reservoir_height <= config.RESERVOIR_CRITICAL_LOW_CM and elapsed_warning >= config.RESPONSE_TIMEOUT_SEC:
                    if not self.auto_fill_active:
                        logger.info("RM-2: Seuil critique atteint (%.1fcm) et délai dépassé. Démarrage remplissage auto.", reservoir_height)
                        self.auto_fill_active = True
                        self.auto_fill_start_time = now
                        self.relays.set_actuator("pump", True, source="rule:RM-2")
            else:
                self.low_warning_active = False
                self.low_warning_time = None

            # Manage running auto-fill pump duration
            if self.auto_fill_active:
                elapsed_fill = (now - self.auto_fill_start_time) if self.auto_fill_start_time else 0
                if elapsed_fill >= config.AUTO_FILL_DURATION_SEC or reservoir_height >= config.RESERVOIR_LOW_THRESHOLD_CM:
                    logger.info("RM-2: Fin du remplissage auto (durée %.1fs / hauteur %.1fcm). Arrêt pompe.", elapsed_fill, reservoir_height)
                    self.auto_fill_active = False
                    self.auto_fill_start_time = None
                    self.relays.set_actuator("pump", False, source="rule:RM-2")

        return {
            "mode": self.mode,
            "actuators": self.relays.get_all_states(),
            "alerts": alerts
        }

    def handle_manual_command(self, cmd_payload: dict) -> dict:
        """
        Handles manual operator commands from Flutter app via FastAPI WebSocket.
        Enforces RM-7 overflow pump lockout. Manual commands cancel RM-2 auto-fill window.
        """
        action = cmd_payload.get("action", "").upper()
        actuator_type = cmd_payload.get("actuator_type", "").lower()
        val = cmd_payload.get("value")

        if action == "SET_MODE":
            mode_val = str(val).upper()
            if mode_val in ["AUTO", "MANUAL"]:
                self.mode = mode_val
                logger.info("Operating mode changed to: %s", self.mode)
                return {"status": "accepted", "mode": self.mode}

        # Manual actuator command
        desired_state = True if (val == "ON" or val is True or val == 1) else False

        # RM-7 Check: Reject pump ON if overflow failsafe is active
        if actuator_type == "pump" and desired_state and self.overflow_failsafe_active:
            logger.warn("RM-7 Reject: Manual pump start rejected due to overflow protection lockout.")
            return {
                "status": "rejected",
                "actuator_type": "pump",
                "desired_state": False,
                "reason": "protection anti-débordement (RM-7)"
            }

        # Manual command during RM-2 alert window cancels auto-fill timer
        if actuator_type == "pump":
            self.low_warning_active = False
            self.auto_fill_active = False

        res = self.relays.set_actuator(actuator_type, desired_state, source="manual")
        return {"status": "accepted", "actuator": res}
