import sys
import os
import time
import logging

# Add src to path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from monitor import WiFiMonitor

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def test_portal(preview_only=False, port=80):
    print("🚀 No WiFi! Denied! - Portal Test Mode")
    if preview_only:
        print(f"Running in PREVIEW MODE (Web Only) on port {port}.")
        print("This will NOT start a hotspot or disconnect your WiFi.")
    else:
        print(f"Running in FULL MODE (Hotspot + Web) on port {port}.")
        print("WARNING: This WILL disconnect your current WiFi/SSH session.")

    print("Press Ctrl+C to stop and cleanup.")
    print("-" * 40)

    monitor = WiFiMonitor()

    try:
        if preview_only:
            # Only start the web portal thread
            import threading
            from web_portal import run_portal, get_submitted_credentials
            from notifier import NotificationManager

            notifier = NotificationManager()
            portal_thread = threading.Thread(
                target=run_portal, kwargs={"port": port}, daemon=True
            )
            portal_thread.start()

            # Get local IP to show the user where to go
            ip = monitor.nm.get_ip_address()
            print("\n✅ Web Portal is running in PREVIEW MODE!")
            print(f"Open your browser and go to: http://{ip}:{port}")
            print("\n💡 TEST EMAIL FEATURE: If you enter an email in the form,")
            print("   the script will attempt to send a test notification.")

            while True:
                # Check for submitted credentials in preview mode
                creds = get_submitted_credentials()
                if creds and creds.get("email"):
                    print(f"\n📧 Sending test email to {creds['email']}...")
                    if notifier.send_connection_success(creds["email"], "TEST_NETWORK", ip):
                        print("✅ Test email sent successfully!")
                    else:
                        print("❌ Failed to send test email. Check config/email_settings.json")
                time.sleep(1)
        else:
            # Force entry into setup mode (Full Hotspot)
            monitor.enter_setup_mode()
            print("\n✅ Portal is now broadcasting!")
            print(f"SSID: {monitor.nm.hotspot_ssid}")
            print("1. Connect your phone/laptop to this WiFi.")
            print("2. Open a browser and go to http://anything.com")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping test and cleaning up...")
        if not preview_only:
            monitor.stop_dnsmasq()
            monitor.nm.stop_hotspot()
        print("Cleanup complete.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test the No WiFi! Denied! portal.")
    parser.add_argument(
        "--preview", action="store_true", help="Run web portal only (no hotspot)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Custom port (default 80 for full, 8080 for preview)",
    )
    args = parser.parse_args()

    is_root = os.geteuid() == 0
    port = args.port

    if args.preview:
        if port is None:
            port = 80 if is_root else 8080
        test_portal(preview_only=True, port=port)
    else:
        # Full mode REQUIRES root
        if not is_root:
            print("❌ Error: Full mode (hotspot) requires sudo.")
            sys.exit(1)
        if port is None:
            port = 80
        test_portal(preview_only=False, port=port)
