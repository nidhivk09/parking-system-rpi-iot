# 🅿️ SmartPark — Raspberry Pi + Firebase Parking System

Real-time parking slot monitoring using HC-SR04 ultrasonic sensors on Raspberry Pi 4, with live data pushed to Firebase and displayed on a React web app.

---

## 📐 Architecture

```
[HC-SR04 Sensors] → [Raspberry Pi 4] → [Firebase Realtime DB] → [React WebApp]
```

---

## 🗂 Project Structure

```
smart-parking-system/
├── raspberry-pi/
│   ├── parking_sensor.py     # Main sensor loop + Firebase push
│   ├── simulator.py          # Test Firebase without hardware
│   ├── requirements.txt      # Python dependencies
│   └── setup.sh              # One-shot Pi setup script
├── webapp/
│   ├── src/
│   │   ├── App.js            # Main React UI component
│   │   ├── App.css           # Dark industrial UI styles
│   │   ├── firebase.js       # Firebase SDK init
│   │   └── index.js          # React entry point
│   ├── public/index.html
│   ├── .env.example          # Firebase env vars template
│   └── package.json
├── .github/workflows/
│   └── deploy.yml            # GitHub Actions → Firebase Hosting
├── firebase.json             # Firebase hosting config
├── firebase.rules.json       # Realtime DB security rules
├── .gitignore
└── README.md
```

---

## 🔌 Hardware Setup

### Compatible IR Sensors
Any of these work out of the box (all use the same 3-pin interface):
- **FC-51** — most common, recommended, ~₹30 each
- **TCRT5000** — reflective, good for close-range detection
- **LM393-based IR obstacle sensor** — adjustable via onboard potentiometer

### Parts
- Raspberry Pi 4 (any RAM)
- IR obstacle sensors — one per parking slot
- Breadboard + jumper wires (no resistors needed — sensors run at 3.3V logic)

### Wiring (per sensor — only 3 wires!)

```
Sensor VCC → Pi 3.3V  (Pin 1 or 17)
Sensor GND → Pi GND   (Pin 6, 9, 14, 20, 25, 30, 34, or 39)
Sensor OUT → Pi GPIO  (BCM pin, one per slot)
```

> ✅ IR sensors operate at 3.3V — plug directly into Pi GPIO with no resistors needed.
> The onboard potentiometer controls detection range (~2–30 cm). Turn clockwise to increase sensitivity.

### How IR Detection Works

```
Car present  → IR beam blocked → OUT = LOW  (0) → OCCUPIED
No car       → IR beam clear   → OUT = HIGH (1) → AVAILABLE
```

### Default Pin Mapping (BCM) — one pin per slot

| Slot    | OUT Pin (BCM) | Physical Pin |
|---------|--------------|--------------|
| Slot A1 | 17           | Pin 11       |
| Slot A2 | 27           | Pin 13       |
| Slot B1 | 22           | Pin 15       |
| Slot B2 | 23           | Pin 16       |

Edit `PARKING_SLOTS` in `parking_sensor.py` to change pins or add more slots.

---

## 🔥 Firebase Setup

1. Go to [Firebase Console](https://console.firebase.google.com/) → **Add Project**
2. Enable **Realtime Database** → Start in test mode
3. Go to **Project Settings → Service Accounts → Generate new private key**
4. Save the downloaded JSON as `raspberry-pi/serviceAccountKey.json`
5. Update `FIREBASE_DATABASE_URL` in `parking_sensor.py`
6. Apply database rules:
   ```bash
   firebase deploy --only database
   ```

---

## 🥧 Raspberry Pi Setup

```bash
cd raspberry-pi/
bash setup.sh
```

Then edit `parking_sensor.py`:
```python
FIREBASE_DATABASE_URL = "https://YOUR-PROJECT-ID-default-rtdb.firebaseio.com/"
```

### Run
```bash
# One-time run
python3 parking_sensor.py

# As a systemd service (auto-starts on boot)
sudo systemctl start smart-parking
sudo journalctl -u smart-parking -f
```

### Test without hardware
```bash
python3 simulator.py
```

---

## 🌐 Web App Setup

```bash
cd webapp/
cp .env.example .env
# Fill in .env with your Firebase project values
npm install
npm start          # Development server → http://localhost:3000
npm run build      # Production build
```

### Deploy to Firebase Hosting
```bash
npm install -g firebase-tools
firebase login
firebase init hosting   # Select existing project, public dir: build
npm run build
firebase deploy
```

---

## 🚀 GitHub Setup

```bash
git init
git add .
git commit -m "Initial commit: Smart Parking System"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/smart-parking-system.git
git push -u origin main
```

### GitHub Actions (Auto-deploy on push)

Add these repository secrets under **Settings → Secrets and variables → Actions**:

| Secret | Value |
|--------|-------|
| `FIREBASE_API_KEY` | From Firebase web app config |
| `FIREBASE_AUTH_DOMAIN` | From Firebase web app config |
| `FIREBASE_DATABASE_URL` | From Firebase web app config |
| `FIREBASE_PROJECT_ID` | From Firebase web app config |
| `FIREBASE_STORAGE_BUCKET` | From Firebase web app config |
| `FIREBASE_MESSAGING_SENDER_ID` | From Firebase web app config |
| `FIREBASE_APP_ID` | From Firebase web app config |
| `FIREBASE_SERVICE_ACCOUNT` | JSON content of service account key |

---

## ⚙️ Customization

### Add more parking slots
In `parking_sensor.py`:
```python
PARKING_SLOTS = {
    "slot_1": {"out": 17, "label": "Gate A - Slot 1"},
    "slot_5": {"out": 24, "label": "Gate B - Slot 1"},
    # One GPIO pin per slot — simple!
}
```

### Flip detection logic (if your sensor is active-high)
```python
IR_ACTIVE_LOW = False   # Set True for FC-51/TCRT5000 (default), False for active-high modules
```

### Adjust debounce sensitivity
```python
DEBOUNCE_COUNT = 3     # Increase to filter more false triggers from ambient IR
POLL_INTERVAL = 1.0    # Read sensors every 1 second
```

---

## 📊 Firebase Data Structure

```json
{
  "parking": {
    "slots": {
      "slot_1": {
        "label": "Slot A1",
        "occupied": true,
        "sensor_type": "IR",
        "status": "occupied"
      }
    },
    "summary": {
      "total": 4,
      "occupied": 2,
      "available": 2,
      "last_updated": "2025-01-15T10:32:00Z"
    }
  }
}
```

---

## 📜 License

MIT — free to use, modify, and deploy.
