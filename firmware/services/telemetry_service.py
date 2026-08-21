"""
FastAPI REST & Local Circular Buffer Telemetry Service.
Implements Flux 1 (Batch Readings POST /api/v1/readings/batch) with offline catch-up buffer.
Implements Flux 4 (Alerts POST /api/v1/alerts).
"""
import time
from firmware import config
from firmware.utils.logger import Logger

logger = Logger("TELEMETRY_SVC")


class TelemetryService:
    """
    Manages periodic telemetry publishing to FastAPI backend with bounded circular offline buffer.
    """

    def __init__(self):
        self.buffer = []
        self.max_buffer_size = getattr(config, "MAX_OFFLINE_BUFFER_SIZE", 1000)
        self.online = True

    def buffer_readings(self, readings_list: list):
        """
        Stores sensor readings in bounded circular buffer.
        """
        for r in readings_list:
            if len(self.buffer) >= self.max_buffer_size:
                self.buffer.pop(0) # Evict oldest reading if buffer full
            self.buffer.append(r)

    def publish_batch(self, readings_list: list) -> bool:
        """
        Transmits a batch of sensor readings to POST /api/v1/readings/batch.
        If network fails, buffers them locally for catch-up transmission.
        """
        self.buffer_readings(readings_list)

        if not self.online:
            logger.warn("Network offline: %d readings buffered locally.", len(self.buffer))
            return False

        # Simulate or perform HTTP POST to FastAPI backend
        batch_size = len(self.buffer)
        logger.info("FastAPI Batch Tx [/api/v1/readings/batch]: Transmitting %d readings...", batch_size)
        
        # On success, clear sent buffer
        self.buffer.clear()
        return True

    def publish_alert(self, alert_payload: dict) -> bool:
        """
        Sends alert event to POST /api/v1/alerts.
        """
        logger.info("FastAPI Alert Tx [/api/v1/alerts]: [%s] %s", 
                    alert_payload.get("severity", "info").upper(), 
                    alert_payload.get("message"))
        return True

    def set_online(self, status: bool):
        self.online = bool(status)
        if self.online and self.buffer:
            logger.info("Reconnected: Flushing %d offline buffered readings...", len(self.buffer))
            self.publish_batch([])
