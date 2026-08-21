"""
MicroPython 'network' module mock for desktop CPython simulation.
"""

STA_IF = 0
AP_IF = 1

class WLAN:
    def __init__(self, interface_id=STA_IF):
        self.interface_id = interface_id
        self._active = False
        self._connected = True

    def active(self, is_active=None):
        if is_active is not None:
            self._active = bool(is_active)
        return self._active

    def connect(self, ssid, password):
        self._connected = True
        return True

    def disconnect(self):
        self._connected = False

    def isconnected(self):
        return self._connected

    def ifconfig(self, config_tuple=None):
        return ('192.168.1.105', '255.255.255.0', '192.168.1.1', '8.8.8.8')
