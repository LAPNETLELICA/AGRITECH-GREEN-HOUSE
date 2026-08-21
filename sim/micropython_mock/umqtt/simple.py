"""
MicroPython 'umqtt.simple' module mock for desktop CPython simulation.
Connects directly to the in-memory Mock MQTT Broker or logs messages.
"""
from sim.mqtt_broker_mock import get_mock_mqtt_broker

class MQTTClient:
    def __init__(self, client_id, server, port=1883, user=None, password=None, keepalive=60, ssl=False, ssl_params={}):
        self.client_id = client_id
        self.server = server
        self.port = port
        self.user = user
        self.password = password
        self.keepalive = keepalive
        self.callback = None
        self.subscribed_topics = []
        self.broker = get_mock_mqtt_broker()

    def set_callback(self, f):
        self.callback = f

    def connect(self, clean_session=True):
        self.broker.register_client(self.client_id, self.callback)
        return 0

    def disconnect(self):
        self.broker.unregister_client(self.client_id)

    def publish(self, topic, msg, retain=False, qos=0):
        topic_str = topic.decode('utf-8') if isinstance(topic, bytes) else str(topic)
        msg_str = msg.decode('utf-8') if isinstance(msg, bytes) else str(msg)
        self.broker.publish(topic_str, msg_str, sender_id=self.client_id)

    def subscribe(self, topic, qos=0):
        topic_str = topic.decode('utf-8') if isinstance(topic, bytes) else str(topic)
        self.subscribed_topics.append(topic_str)
        self.broker.subscribe(self.client_id, topic_str)

    def check_msg(self):
        self.broker.process_queued_messages(self.client_id)

    def wait_msg(self):
        self.check_msg()
