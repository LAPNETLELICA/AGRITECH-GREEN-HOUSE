"""
MQTT Telemetry & Command Handling Service for Person A.
"""
import json
from firmware import config
from firmware.utils.logger import Logger

logger = Logger("MQTT_SVC")

try:
    from umqtt.simple import MQTTClient
except ImportError:
    MQTTClient = None

class MQTTService:
    def __init__(self, command_callback=None):
        self.command_callback = command_callback
        self.client = None
        self.connected = False

    def connect(self):
        try:
            if MQTTClient is None:
                logger.info("Simulation mode: Virtual MQTT client active.")
                self.connected = True
                return True

            self.client = MQTTClient(
                client_id=config.MQTT_CLIENT_ID,
                server=config.MQTT_BROKER,
                port=config.MQTT_PORT,
                keepalive=config.MQTT_KEEPALIVE
            )
            
            if self.command_callback:
                self.client.set_callback(self._on_message_internal)

            logger.info("Connecting to MQTT Broker at %s:%d...", config.MQTT_BROKER, config.MQTT_PORT)
            self.client.connect()
            self.connected = True
            logger.info("MQTT connected successfully.")

            # Subscribe to command topics
            self.client.subscribe(config.MQTT_TOPIC_COMMANDS)
            logger.info("Subscribed to command topic: %s", config.MQTT_TOPIC_COMMANDS)
            return True
        except Exception as e:
            logger.warn("MQTT connect failed (broker offline or simulated): %s", str(e))
            self.connected = False
            return False

    def _on_message_internal(self, topic, msg):
        try:
            topic_str = topic.decode('utf-8') if isinstance(topic, bytes) else str(topic)
            msg_str = msg.decode('utf-8') if isinstance(msg, bytes) else str(msg)
            logger.info("MQTT Rx [%s]: %s", topic_str, msg_str)

            data = json.loads(msg_str)
            if self.command_callback:
                self.command_callback(data)
        except Exception as e:
            logger.error("Error processing incoming MQTT message: %s", str(e))

    def publish_telemetry(self, payload_dict):
        payload_json = json.dumps(payload_dict)
        if self.client and self.connected:
            try:
                self.client.publish(config.MQTT_TOPIC_TELEMETRY, payload_json)
                logger.debug("MQTT Telemetry Tx: %s", payload_json)
                return True
            except Exception as e:
                logger.warn("Failed to publish MQTT telemetry: %s", str(e))
                self.connected = False
                return False
        else:
            logger.debug("[SIM] MQTT Telemetry Tx -> %s: %s", config.MQTT_TOPIC_TELEMETRY, payload_json)
            return True

    def publish_alert(self, alert_msg):
        payload = json.dumps({"device_id": config.DEVICE_ID, "alert": alert_msg})
        if self.client and self.connected:
            try:
                self.client.publish(config.MQTT_TOPIC_ALERTS, payload)
            except Exception:
                pass

    def check_messages(self):
        """
        Polls for incoming MQTT messages on subscribed topics.
        """
        if self.client and self.connected:
            try:
                self.client.check_msg()
            except Exception as e:
                logger.warn("MQTT message check error: %s", str(e))
