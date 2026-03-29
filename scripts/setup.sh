#!/bin/bash

# No WiFi! Denied! - Setup Script
# This script installs dependencies and configures the systemd service.

set -e

echo "📶 No WiFi! Denied! - Setup"

# 1. Update system and install dependencies
echo "Installing dependencies..."
sudo apt update
sudo apt install -y python3-flask dnsmasq network-manager psmisc

# 2. Create systemd service
SERVICE_PATH="/etc/systemd/system/nowifidenied.service"
APP_DIR=$(pwd)

echo "Creating systemd service at $SERVICE_PATH..."
sudo bash -c "cat > $SERVICE_PATH" <<EOF
[Unit]
Description=No WiFi! Denied! - WiFi Connection Monitor and Portal
After=network.target NetworkManager.service

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/python3 $APP_DIR/src/monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 3. Reload systemd and enable service
echo "Enabling and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable nowifidenied.service
# We don't start it immediately to give the user a chance to check everything
# sudo systemctl start nowifidenied.service

echo "Done! You can start the service with: sudo systemctl start nowifidenied.service"
echo "Check logs with: journalctl -u nowifidenied.service -f"
