"""
Smart Parking System — IR Sensor Simulator
Use this to test Firebase integration without physical hardware.
Simulates digital IR sensor output (occupied/available) — no distance values.
Run: python3 simulator.py
"""

import time
import random
import logging
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db

FIREBASE_CREDENTIALS_PATH = "serviceAccountKey.json"
FIREBASE_DATABASE_URL = "https://YOUR-PROJECT-ID-default-rtdb.firebaseio.com/"

PARKING_SLOTS = {
    "slot_1": {"label": "Slot A1"},
    "slot_2": {"label": "Slot A2"},
    "slot_3": {"label": "Slot B1"},
    "slot_4": {"label": "Slot B2"},
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

def init_firebase():
    cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_DATABASE_URL})
    log.info("Firebase initialized.")

def simulate_push():
    timestamp = datetime.utcnow().isoformat() + "Z"
    slot_data = {}
    for slot_id, info in PARKING_SLOTS.items():
        # IR sensor gives a simple digital HIGH/LOW — no distance measurement
        occupied = random.choice([True, False])
        slot_data[slot_id] = {
            "label": info["label"],
            "occupied": occupied,
            "sensor_type": "IR",
            "status": "occupied" if occupied else "available",
        }

    total = len(slot_data)
    occupied_count = sum(1 for s in slot_data.values() if s["occupied"])

    payload = {
        "slots": slot_data,
        "summary": {
            "total": total,
            "occupied": occupied_count,
            "available": total - occupied_count,
            "last_updated": timestamp,
        }
    }

    db.reference("parking").set(payload)
    log.info(f"[SIM] Pushed: {total - occupied_count}/{total} available")

if __name__ == "__main__":
    log.info("=== IR Sensor Simulator Starting (Ctrl+C to stop) ===")
    init_firebase()
    try:
        while True:
            simulate_push()
            time.sleep(3)
    except KeyboardInterrupt:
        log.info("Simulator stopped.")
