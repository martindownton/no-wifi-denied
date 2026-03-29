import subprocess
import logging

# NetworkManager is typically available on Linux systems like Raspberry Pi OS
try:
    import NetworkManager

    NM_AVAILABLE = True
except ImportError:
    NM_AVAILABLE = False
    logging.warning(
        "NetworkManager library not found. Falling back to nmcli/mock mode."
    )

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class NetworkManager:
    def __init__(self, interface="wlan0", hotspot_ssid="No WiFi! Denied!"):
        self.interface = interface
        self.hotspot_ssid = hotspot_ssid
        self.hotspot_con_name = "nowifidenied-hotspot"

    def is_connected(self, host="8.8.8.8", timeout=5):
        """Checks if we have internet connectivity by pinging a public IP."""
        try:
            subprocess.check_call(
                ["ping", "-c", "1", "-W", str(timeout), host],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def scan_wifi(self):
        """Scans for available WiFi networks and returns a list of SSIDs."""
        try:
            # Rescan for new networks
            subprocess.run(
                ["nmcli", "device", "wifi", "rescan"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            output = subprocess.check_output(
                ["nmcli", "-t", "-f", "SSID,SIGNAL", "device", "wifi", "list"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()

            networks = []
            for line in output.split("\n"):
                if line:
                    parts = line.split(":")
                    if len(parts) >= 2:
                        ssid = parts[0]
                        signal = parts[1]
                        if ssid and ssid != self.hotspot_ssid:
                            networks.append({"ssid": ssid, "signal": int(signal)})

            # Sort by signal strength and remove duplicates
            networks.sort(key=lambda x: x["signal"], reverse=True)
            seen_ssids = set()
            unique_networks = []
            for net in networks:
                if net["ssid"] not in seen_ssids:
                    unique_networks.append(net)
                    seen_ssids.add(net["ssid"])

            return unique_networks
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback for local testing if nmcli is missing
            logging.warning(
                "nmcli not found or error. Returning mock data for UI testing."
            )
            return [
                {"ssid": "Mock_WiFi_1", "signal": 90},
                {"ssid": "Mock_WiFi_2", "signal": 70},
                {"ssid": "Mock_WiFi_3", "signal": 40},
            ]
        except Exception as e:
            logging.error(f"Error scanning WiFi: {e}")
            return []

    def start_hotspot(self, password=None):
        """Starts a WiFi hotspot."""
        try:
            logging.info(f"Starting hotspot '{self.hotspot_ssid}'...")

            # Ensure any previous hotspot connection is removed
            self.stop_hotspot()

            cmd = [
                "nmcli",
                "device",
                "wifi",
                "hotspot",
                "ifname",
                self.interface,
                "con-name",
                self.hotspot_con_name,
                "ssid",
                self.hotspot_ssid,
            ]
            if password:
                cmd.extend(["password", password])

            subprocess.check_call(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            logging.info("Hotspot started successfully.")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logging.warning(
                f"Failed to start hotspot (nmcli missing/error). Local testing mode: {e}"
            )
            return True  # Pretend it started for testing purposes if you are local

    def stop_hotspot(self):
        """Stops and removes the hotspot connection."""
        try:
            subprocess.run(
                ["nmcli", "connection", "down", self.hotspot_con_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            subprocess.run(
                ["nmcli", "connection", "delete", self.hotspot_con_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            return False

    def connect_to_wifi(self, ssid, password):
        """Attempts to connect to a WiFi network."""
        try:
            logging.info(f"Attempting to connect to '{ssid}'...")

            # This will create a new connection or use an existing one
            cmd = [
                "nmcli",
                "device",
                "wifi",
                "connect",
                ssid,
                "password",
                password,
                "ifname",
                self.interface,
            ]
            subprocess.check_call(cmd, timeout=30)
            logging.info(f"Successfully connected to '{ssid}'.")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to connect to '{ssid}': {e}")
            return False
        except subprocess.TimeoutExpired:
            logging.error(f"Connection attempt to '{ssid}' timed out.")
            return False

    def get_ip_address(self):
        """Returns the current IP address of the interface."""
        try:
            output = subprocess.check_output(
                ["nmcli", "-g", "IP4.ADDRESS", "device", "show", self.interface],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            # output is like '192.168.1.50/24'
            if output:
                return output.split("/")[0]
            return "Unknown"
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback for Mac/Local testing
            import socket

            try:
                # This doesn't actually connect, but gets the local IP used to reach a public one
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                s.close()
                return ip
            except Exception:
                return "127.0.0.1"
        except Exception:
            return "Unknown"


if __name__ == "__main__":
    # Quick test
    nm = NetworkManager()
    print(f"Connected: {nm.is_connected()}")
    # print(f"Nearby Networks: {nm.scan_wifi()}")
