"""
Smart Parking System - Raspberry Pi Sensor Script
Uses IR obstacle sensors (FC-51 / TCRT5000 / LM393-based) to detect
parking slot occupancy and pushes data to Firebase Realtime Database.

IR Sensor Logic:
  - OUT pin → LOW  (0) when an obstacle IS detected   → slot OCCUPIED
  - OUT pin → HIGH (1) when no obstacle detected       → slot AVAILABLE

Most IR modules have an onboard LED that lights up when an obstacle is
detected, and a potentiometer to adjust detection sensitivity/range.
"""

import RPi.GPIO as GPIO
import time
import logging
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

FIREBASE_CREDENTIALS_PATH = "serviceAccountKey.json"
FIREBASE_DATABASE_URL = "https://YOUR-PROJECT-ID-default-rtdb.firebaseio.com/"

# Parking slots: each slot has a single OUT pin from the IR sensor.
# The IR sensor only needs VCC, GND, and OUT — one GPIO pin per slot.
# Add/remove slots as needed.
PARKING_SLOTS = {
    "slot_1": {"out": 17, "label": "Slot A1"},
    "slot_2": {"out": 27, "label": "Slot A2"},
    "slot_3": {"out": 22, "label": "Slot A3"},
}

# IR sensors output LOW when obstacle detected (active-low).
# Set to False if your module outputs HIGH on detection (active-high).
IR_ACTIVE_LOW = True

# How often to poll sensors (seconds)
POLL_INTERVAL = 1.0

# Debounce: number of consecutive identical reads before state is accepted.
# Helps filter out brief false triggers from ambient IR interference.
DEBOUNCE_COUNT = 3

# ─────────────────────────────────────────────
# LOGGING SETUP
# ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("parking.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# GPIO SETUP
# ─────────────────────────────────────────────

def setup_gpio():
    """Configure all IR sensor OUT pins as inputs with pull-up resistors."""
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for slot_id, cfg in PARKING_SLOTS.items():
        # pull_up_down=GPIO.PUD_UP keeps the line stable when sensor is idle
        GPIO.setup(cfg["out"], GPIO.IN, pull_up_down=GPIO.PUD_UP)
        log.info(f"GPIO initialized for {slot_id} — IR OUT on BCM {cfg['out']}")
    time.sleep(0.2)

# ─────────────────────────────────────────────
# SENSOR READING
# ─────────────────────────────────────────────

def read_ir_sensor(out_pin: int) -> bool:
    """
    Read a single IR sensor.
    Returns True if an obstacle is detected (slot is OCCUPIED), False otherwise.

    Most FC-51 / TCRT5000 modules:
      OUT = 0 (LOW)  → obstacle present → OCCUPIED
      OUT = 1 (HIGH) → clear            → AVAILABLE
    """
    raw = GPIO.input(out_pin)
    if IR_ACTIVE_LOW:
        return raw == GPIO.LOW   # LOW means obstacle detected
    else:
        return raw == GPIO.HIGH  # HIGH means obstacle detected


def debounced_read(out_pin: int) -> bool:
    """
    Read the IR sensor DEBOUNCE_COUNT times in quick succession.
    Only accepts the reading if all samples agree, preventing false triggers.
    """
    readings = [read_ir_sensor(out_pin) for _ in range(DEBOUNCE_COUNT)]
    return all(readings)  # True only if ALL reads agree on occupied

# ─────────────────────────────────────────────
# FIREBASE SETUP
# ─────────────────────────────────────────────

def init_firebase():
    cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_DATABASE_URL})
    log.info("Firebase initialized successfully.")

def push_to_firebase(slot_data: dict):
    """Push the full parking status snapshot to Firebase."""
    timestamp = datetime.utcnow().isoformat() + "Z"
    total_slots = len(slot_data)
    occupied_count = sum(1 for s in slot_data.values() if s["occupied"])
    available_count = total_slots - occupied_count

    payload = {
        "slots": slot_data,
        "summary": {
            "total": total_slots,
            "occupied": occupied_count,
            "available": available_count,
            "last_updated": timestamp,
        }
    }

    ref = db.reference("parking")
    ref.set(payload)
    log.info(f"Firebase updated — {available_count}/{total_slots} available @ {timestamp}")

# ─────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────

def run():
    log.info("=== Smart Parking System (IR Sensors) Starting ===")
    setup_gpio()
    init_firebase()

    previous_states = {}

    try:
        while True:
            slot_data = {}
            changed = False

            for slot_id, cfg in PARKING_SLOTS.items():
                occupied = debounced_read(cfg["out"])

                slot_data[slot_id] = {
                    "label": cfg["label"],
                    "occupied": occupied,
                    "sensor_type": "IR",
                    "status": "occupied" if occupied else "available",
                }

                prev = previous_states.get(slot_id)
                if prev != occupied:
                    changed = True
                    state_str = "OCCUPIED" if occupied else "AVAILABLE"
                    log.info(f"{cfg['label']} (BCM {cfg['out']}) → {state_str}")
                    previous_states[slot_id] = occupied

            if changed:
                push_to_firebase(slot_data)

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        log.info("Shutting down gracefully...")
    finally:
        GPIO.cleanup()
        log.info("GPIO cleaned up.")

if __name__ == "__main__":
    run()
