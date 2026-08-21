"""
Logger Utility for MicroPython / CPython dual compatibility.
"""
import sys
import time

class Logger:
    DEBUG = 0
    INFO = 1
    WARN = 2
    ERROR = 3

    LEVEL_NAMES = {
        DEBUG: "DEBUG",
        INFO: "INFO",
        WARN: "WARN",
        ERROR: "ERROR"
    }

    def __init__(self, name="SYS", level=INFO):
        self.name = name
        self.level = level

    def _get_timestamp(self):
        try:
            # MicroPython ticks_ms
            ms = time.ticks_ms()
            return "{:.3f}s".format(ms / 1000.0)
        except AttributeError:
            # Fallback to CPython time.time()
            return "{:.3f}s".format(time.time() % 1000)

    def _log(self, level, msg, *args):
        if level < self.level:
            return
        lvl_str = self.LEVEL_NAMES.get(level, "INFO")
        ts = self._get_timestamp()
        if args:
            try:
                formatted_msg = msg % args
            except Exception:
                formatted_msg = "{} {}".format(msg, args)
        else:
            formatted_msg = str(msg)
        
        output = "[{}] [{}] [{}] {}".format(ts, lvl_str, self.name, formatted_msg)
        print(output)
        sys.stdout.flush() if hasattr(sys.stdout, "flush") else None

    def debug(self, msg, *args):
        self._log(self.DEBUG, msg, *args)

    def info(self, msg, *args):
        self._log(self.INFO, msg, *args)

    def warn(self, msg, *args):
        self._log(self.WARN, msg, *args)

    def error(self, msg, *args):
        self._log(self.ERROR, msg, *args)

logger = Logger("MAIN")
