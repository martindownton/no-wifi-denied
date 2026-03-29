from flask import Flask, render_template, request, jsonify, redirect
import threading
import logging
from network_manager import NetworkManager

app = Flask(__name__)
nm = NetworkManager()

# Global state to store submitted credentials
submitted_credentials = None
creds_lock = threading.Lock()


@app.route("/")
@app.route("/<path:path>")
def catch_all(path=None):
    # This acts as the captive portal entry point
    # If they are hitting /scan or /connect, they should be handled by their respective routes
    if path in ["scan", "connect"]:
        return None  # Flask will continue to the next match
    return render_template("index.html")


@app.route("/scan")
def scan():
    networks = nm.scan_wifi()
    return jsonify(networks)


@app.route("/connect", methods=["POST"])
def connect():
    global submitted_credentials
    ssid = request.form.get("ssid")
    password = request.form.get("password")
    email = request.form.get("email")

    if ssid and password:
        with creds_lock:
            submitted_credentials = {"ssid": ssid, "password": password, "email": email}
        return """
        <html>
            <head><meta http-equiv="refresh" content="5;url=/"></head>
            <body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
                <h1>Connecting to WiFi...</h1>
                <p>The hotspot will disconnect shortly. If connection fails, the portal will reappear.</p>
            </body>
        </html>
        """
    return redirect("/")


def get_submitted_credentials():
    global submitted_credentials
    with creds_lock:
        creds = submitted_credentials
        submitted_credentials = None
        return creds


def run_portal(host="0.0.0.0", port=80):
    # Flask normally runs in the foreground
    logging.info(f"Starting web portal on {host}:{port}")
    app.run(host=host, port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    run_portal()
