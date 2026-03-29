# 📶 No WiFi! Denied!

"No WiFi! Denied!" is a lightweight utility for Raspberry Pi that ensures your device stays connected to the internet. If it detects a lost connection, it automatically broadcasts a WiFi hotspot with a captive portal, allowing you to easily enter new WiFi credentials from your phone or computer.

## Features

- **Automated Monitoring**: Periodically checks for internet connectivity.
- **Setup Hotspot**: If no connection is found, it creates a "No WiFi! Denied!" hotspot.
- **Captive Portal**: Automatically redirects connected users to a setup page.
- **Email Notifications**: Optionally receive an email with your Pi's new local IP address once it connects.
- **Modern Backend**: Built for Raspberry Pi OS (Bookworm) using `NetworkManager`.
- **Headless-First**: Perfect for IoT projects without a monitor.

## Installation

1. Clone or copy this repository to your Raspberry Pi.
2. Make the setup script executable:
   ```bash
   chmod +x scripts/setup.sh
   ```
3. Run the setup script (requires sudo):
   ```bash
   sudo ./scripts/setup.sh
   ```
4. Start the service:
   ```bash
   sudo systemctl start nowifidenied.service
   ```

## How It Works

1. **Monitor Mode**: The script pings `8.8.8.8` every 30 seconds.
2. **Setup Mode**: After 3 failures, it:
   - Disables the current WiFi connection.
   - Starts a hotspot named "No WiFi! Denied!".
   - Starts a DNS server (`dnsmasq`) to hijack all requests.
   - Starts a web server (`Flask`) on port 80.
3. **Configuration**: 
   - You connect your phone to "No WiFi! Denied!".
   - A setup page appears (or you browse to `http://anything.com`).
   - You select your WiFi network, enter the password, and click "Connect".
4. **Reconnection**: The script stops the hotspot, applies the new credentials, and attempts to connect. If successful, it returns to **Monitor Mode**.

## Email Notifications (Optional)

To enable email notifications:
1. Create a file at `config/email_settings.json` with the following format:
   ```json
   {
     "smtp_server": "smtp.gmail.com",
     "smtp_port": 587,
     "smtp_user": "your-email@gmail.com",
     "smtp_password": "your-app-password"
   }
   ```
   *Note: If using Gmail, you must use an [App Password](https://myaccount.google.com/apppasswords).*
2. During setup, enter your email in the "Notify me at" field.
3. Once the Pi connects, it will email you its new local IP address.

## Dependencies

- Python 3
- `flask`
- `dnsmasq`
- `NetworkManager` (`nmcli`)
- `smtplib` (built-in)

## Testing the Interface

If you want to test the portal UI safely without losing your SSH connection:
1. Run the test script in **Preview Mode**:
   ```bash
   sudo python3 scripts/test_portal.py --preview
   ```
2. Open your browser and visit your Raspberry Pi's IP address (e.g., `http://192.168.1.50`).

To test the **Full Mode** (broadcasts a real hotspot, will disconnect SSH):
1. Run the test script in **Full Mode**:
   ```bash
   sudo python3 scripts/test_portal.py
   ```
2. Connect your phone/laptop to the "No WiFi! Denied!" hotspot.
3. Open a browser and visit any URL (e.g., `http://neverssl.com`).
4. Press `Ctrl+C` when finished to stop the hotspot and cleanup.

## Logs

You can monitor the service's activity with:
```bash
journalctl -u nowifidenied.service -f
```
