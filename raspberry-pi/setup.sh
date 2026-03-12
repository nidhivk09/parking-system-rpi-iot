#!/bin/bash
# ─────────────────────────────────────────────────────────────
# Smart Parking System — Raspberry Pi Setup Script
# Run as: bash setup.sh
# ─────────────────────────────────────────────────────────────

set -e

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   Smart Parking System — Pi Setup Script     ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# Update system
echo "[1/5] Updating system packages..."
sudo apt-get update -qq && sudo apt-get upgrade -y -qq

# Install Python and pip
echo "[2/5] Installing Python dependencies..."
sudo apt-get install -y python3 python3-pip python3-venv -qq

# Create virtual environment
echo "[3/5] Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python packages
echo "[4/5] Installing Python packages..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Setup systemd service for auto-start
echo "[5/5] Setting up systemd service..."
SERVICE_FILE="/etc/systemd/system/smart-parking.service"
WORKING_DIR="$(pwd)"

sudo bash -c "cat > $SERVICE_FILE" << EOF
[Unit]
Description=Smart Parking System
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=$WORKING_DIR
ExecStart=$WORKING_DIR/venv/bin/python3 parking_sensor.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable smart-parking.service

echo ""
echo "✅ Setup complete!"
echo ""
echo "⚠️  IMPORTANT: Place your Firebase serviceAccountKey.json in this directory."
echo "   Then edit parking_sensor.py to set your FIREBASE_DATABASE_URL."
echo ""
echo "Commands:"
echo "  Start:   sudo systemctl start smart-parking"
echo "  Stop:    sudo systemctl stop smart-parking"
echo "  Logs:    sudo journalctl -u smart-parking -f"
echo "  Status:  sudo systemctl status smart-parking"
echo ""
