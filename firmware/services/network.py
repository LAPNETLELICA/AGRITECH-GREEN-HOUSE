"""
Wi-Fi Network Manager for MicroPython ESP32.
"""
import time
from firmware import config
from firmware.utils.logger import Logger

logger = Logger("NETWORK")

try:
    import network
except ImportError:
    network = None

class NetworkManager:
    def __init__(self, ssid=config.WIFI_SSID, password=config.WIFI_PASS):
        self.ssid = ssid
        self.password = password
        self.wlan = None
        self.is_connected = False

    def connect(self, timeout=config.WIFI_CONNECT_TIMEOUT_SEC):
        if network is None:
            logger.info("Simulation mode: Virtual Wi-Fi interface connected.")
            self.is_connected = True
            return True

        try:
            self.wlan = network.WLAN(network.STA_IF)
            self.wlan.active(True)

            if self.wlan.isconnected():
                logger.info("Already connected to Wi-Fi. IP: %s", self.wlan.ifconfig()[0])
                self.is_connected = True
                return True

            logger.info("Connecting to Wi-Fi SSID '%s'...", self.ssid)
            self.wlan.connect(self.ssid, self.password)

            start_t = time.time() if hasattr(time, "time") else 0
            while not self.wlan.isconnected():
                now = time.time() if hasattr(time, "time") else 0
                if (now - start_t) > timeout:
                    logger.warn("Wi-Fi connection attempt timed out!")
                    self.is_connected = False
                    return False
                time.sleep(0.5)

            ip = self.wlan.ifconfig()[0]
            logger.info("Wi-Fi connected successfully! Local IP: %s", ip)
            self.is_connected = True
            return True
        except Exception as e:
            logger.error("Wi-Fi connection error: %s", str(e))
            self.is_connected = False
            return False

    def check_connection(self):
        if self.wlan is not None:
            self.is_connected = self.wlan.isconnected()
        return self.is_connected
