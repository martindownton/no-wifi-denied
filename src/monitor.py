import time
import logging
import threading
import subprocess
import os
from network_manager import NetworkManager
from web_portal import run_portal, get_submitted_credentials
from notifier import NotificationManager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class WiFiMonitor:
    def __init__(self):
        self.nm = NetworkManager()
        self.notifier = NotificationManager()
        self.setup_mode = False
        self.check_interval = 30  # seconds
        self.failure_threshold = 3
        self.failure_count = 0
        self.portal_thread = None

    def start_dnsmasq(self):
        """Starts dnsmasq to redirect all DNS queries to this Pi."""
        logging.info("Starting dnsmasq for DNS hijacking...")
        config_path = os.path.join(os.getcwd(), "config", "dnsmasq.conf")
        # Create config if it doesn't exist
        os.makedirs("config", exist_ok=True)
        with open(config_path, "w") as f:
            # address=/#/10.42.0.1 maps all domains to the Pi's hotspot IP
            f.write("interface=wlan0\n")
            f.write("address=/#/10.42.0.1\n")
            f.write("bind-interfaces\n")
            f.write("no-dhcp-interface=wlan0\n")  # NM handles DHCP
            f.write("port=53\n")

        try:
            subprocess.run(
                ["killall", "dnsmasq"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            subprocess.Popen(
                ["dnsmasq", "-C", config_path, "-d"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            logging.error(f"Failed to start dnsmasq: {e}")

    def stop_dnsmasq(self):
        logging.info("Stopping dnsmasq...")
        subprocess.run(
            ["killall", "dnsmasq"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

    def enter_setup_mode(self):
        if self.setup_mode:
            return

        logging.info("--- ENTERING SETUP MODE ---")
        self.setup_mode = True

        # 1. Start Hotspot
        if self.nm.start_hotspot():
            # 2. Start DNS redirection
            self.start_dnsmasq()

            # 3. Start Web Portal (in a thread if not already running)
            if not self.portal_thread or not self.portal_thread.is_alive():
                self.portal_thread = threading.Thread(
                    target=run_portal, kwargs={"port": 80}, daemon=True
                )
                self.portal_thread.start()

            logging.info("Setup mode active. Waiting for credentials...")
        else:
            logging.error("Failed to enter setup mode (hotspot failed to start).")
            self.setup_mode = False

    def exit_setup_mode(self):
        logging.info("--- EXITING SETUP MODE ---")
        self.stop_dnsmasq()
        self.nm.stop_hotspot()
        self.setup_mode = False
        # Flask thread remains (daemonic), but is unreachable without hotspot

    def run(self):
        logging.info("WiFi Monitor Service Started.")

        while True:
            if not self.setup_mode:
                if self.nm.is_connected():
                    if self.failure_count > 0:
                        logging.info("Connectivity restored.")
                    self.failure_count = 0
                else:
                    self.failure_count += 1
                    logging.warning(
                        f"Connectivity check failed ({self.failure_count}/{self.failure_threshold})"
                    )

                    if self.failure_count >= self.failure_threshold:
                        self.enter_setup_mode()

            else:
                # We are in setup mode, check if credentials were submitted
                creds = get_submitted_credentials()
                if creds:
                    logging.info(
                        f"Received credentials for '{creds['ssid']}'. Attempting to connect..."
                    )

                    # Temporarily stop hotspot to use wlan0 for connection
                    self.stop_dnsmasq()
                    self.nm.stop_hotspot()

                    if self.nm.connect_to_wifi(creds["ssid"], creds["password"]):
                        logging.info("Connection successful!")
                        self.exit_setup_mode()  # cleanup and return to monitor

                        # Send success email if address provided
                        if creds.get("email"):
                            # Wait a few seconds for DHCP to settle and get an IP
                            time.sleep(5)
                            ip = self.nm.get_ip_address()
                            self.notifier.send_connection_success(
                                creds["email"], creds["ssid"], ip
                            )
                    else:
                        logging.error("Connection failed. Returning to setup mode.")

                        # Send failure email if address provided and we have SOME internet (rare case)
                        # or just wait for next successful connection.
                        # For now, we'll try to send it if there's any available connection
                        if creds.get("email") and self.nm.is_connected():
                            self.notifier.send_connection_failure(
                                creds["email"], creds["ssid"]
                            )

                        self.setup_mode = False  # Force re-entry to restart everything
                        self.enter_setup_mode()

            time.sleep(self.check_interval)


if __name__ == "__main__":
    monitor = WiFiMonitor()
    try:
        monitor.run()
    except KeyboardInterrupt:
        logging.info("Service stopping...")
        monitor.stop_dnsmasq()
        monitor.nm.stop_hotspot()
