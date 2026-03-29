import sys
import os
import time
import logging

# Add src to path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from monitor import WiFiMonitor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_portal(preview_only=False):
    print("🚀 No WiFi! Denied! - Portal Test Mode")
    if preview_only:
        print("Running in PREVIEW MODE (Web Only).")
        print("This will NOT start a hotspot or disconnect your WiFi.")
    else:
        print("Running in FULL MODE (Hotspot + Web).")
        print("WARNING: This WILL disconnect your current WiFi/SSH session.")
    
    print("Press Ctrl+C to stop and cleanup.")
    print("-" * 40)

    monitor = WiFiMonitor()
    
    try:
        if preview_only:
            # Only start the web portal thread
            import threading
            from web_portal import run_portal
            portal_thread = threading.Thread(target=run_portal, kwargs={'port': 80}, daemon=True)
            portal_thread.start()
            
            # Get local IP to show the user where to go
            ip = monitor.nm.get_ip_address()
            print(f"\n✅ Web Portal is running!")
            print(f"Open your browser and go to: http://{ip}")
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

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Test the No WiFi! Denied! portal.")
    parser.add_argument('--preview', action='store_true', help="Run web portal only (no hotspot)")
    args = parser.parse_args()

    # Ensure we are running as root/sudo since port 80 requires it
    if os.geteuid() != 0:
        print("❌ Error: This script must be run with sudo.")
        sys.exit(1)
        
    test_portal(preview_only=args.preview)
