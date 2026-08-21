"""
MicroPython Boot Script - AGRITECH GREENHOUSE (Person A)
Runs system initialization tasks, garbage collection configuration, and boot checks.
"""
import sys
import gc

# Enable automatic garbage collection
gc.enable()

print("\n" + "="*60)
print("  AGRITECH GREENHOUSE - PERSON A FIRMWARE BOOTING")
print("  Node: Climate & Environmental Sensing Controller")
print("="*60 + "\n")

try:
    import esp
    esp.osdebug(None) # Disable debug messages from low-level ESP OS
except Exception:
    pass

# Run garbage collection after boot initialization
gc.collect()
print("[BOOT] System heap memory initialized. Free heap: {} bytes".format(gc.mem_free()))
