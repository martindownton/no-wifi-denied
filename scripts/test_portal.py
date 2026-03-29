import sys
import os
import time
import logging

# Add src to path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from monitor import WiFiMonitor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_portal():
    print("🚀 No WiFi! Denied! - Portal Test Mode")
    print("This script will force the hotspot and web portal to start for testing.")
    print("Press Ctrl+C to stop and cleanup.")
    print("-" * 40)

    monitor = WiFiMonitor()
    
    try:
        # Force entry into setup mode
        monitor.enter_setup_mode()
        
        print("\n✅ Portal is now broadcasting!")
        print(f"SSID: {monitor.nm.hotspot_ssid}")
        print("1. Connect your phone/laptop to this WiFi.")
        print("2. Open a browser and go to http://anything.com (if it doesn't pop up automatically).")
        print("3. Test the interface.")
        
        while True:
            # We don't want to actually connect and shut down, 
            # so we just loop and keep it alive.
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping test and cleaning up...")
        monitor.stop_dnsmasq()
        monitor.nm.stop_hotspot()
        print("Cleanup complete.")

if __name__ == '__main__':
    # Ensure we are running as root/sudo since nmcli and dnsmasq require it
    if os.geteuid() != 0:
        print("❌ Error: This script must be run with sudo.")
        sys.exit(1)
    test_portal()
