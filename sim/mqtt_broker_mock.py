"""
In-Memory Mock MQTT Broker for standalone local simulation without external dependencies.
"""
from collections import defaultdict, deque

class MockMQTTBroker:
    def __init__(self):
        self.clients = {} # client_id -> callback
        self.subscriptions = defaultdict(set) # topic -> set of client_ids
        self.queues = defaultdict(deque) # client_id -> deque of (topic, msg)
        self.message_history = deque(maxlen=100)

    def register_client(self, client_id, callback):
        self.clients[client_id] = callback

    def unregister_client(self, client_id):
        if client_id in self.clients:
            del self.clients[client_id]

    def subscribe(self, client_id, topic):
        self.subscriptions[topic].add(client_id)

    def publish(self, topic, msg, sender_id="SYSTEM"):
        self.message_history.append((topic, msg, sender_id))

        # Deliver to all clients subscribed to topic or wildcard
        for sub_topic, subscriber_set in self.subscriptions.items():
            if self._topic_matches(sub_topic, topic):
                for client_id in subscriber_set:
                    self.queues[client_id].append((topic, msg))

    def _topic_matches(self, pattern, topic):
        if pattern == topic or pattern == "#":
            return True
        return False

    def process_queued_messages(self, client_id):
        callback = self.clients.get(client_id)
        queue = self.queues[client_id]
        while queue:
            topic, msg = queue.popleft()
            if callback:
                try:
                    callback(topic, msg)
                except Exception as e:
                    print("[MOCK MQTT] Error executing callback for client {}: {}".format(client_id, e))

    def get_history(self):
        return list(self.message_history)

_broker_instance = MockMQTTBroker()

def get_mock_mqtt_broker():
    return _broker_instance
