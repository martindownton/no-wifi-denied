import smtplib
import json
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class NotificationManager:
    def __init__(self, config_path='config/email_settings.json'):
        self.config_path = config_path
        self.settings = self._load_settings()

    def _load_settings(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Error loading email settings: {e}")
        return None

    def send_connection_success(self, recipient_email, ssid, ip_address):
        if not self.settings:
            logging.warning("Email settings not configured. Skipping notification.")
            return False

        subject = "📶 No WiFi! Denied! - WiFi Connected"
        body = f"""
        Hello!
        
        The Raspberry Pi has successfully connected to: {ssid}
        
        Local IP Address: {ip_address}
        
        You can now access your Pi on the network.
        """
        return self._send_email(recipient_email, subject, body)

    def send_connection_failure(self, recipient_email, ssid):
        if not self.settings:
            return False

        subject = "❌ No WiFi! Denied! - WiFi Connection Failed"
        body = f"""
        Hello!
        
        The Raspberry Pi failed to connect to: {ssid}.
        
        It is returning to Setup Mode. Please try again or provide different credentials.
        """
        return self._send_email(recipient_email, subject, body)

    def _send_email(self, recipient_email, subject, body):
        try:
            msg = MIMEMultipart()
            msg['From'] = self.settings['smtp_user']
            msg['To'] = recipient_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(self.settings['smtp_server'], self.settings['smtp_port']) as server:
                server.starttls()
                server.login(self.settings['smtp_user'], self.settings['smtp_password'])
                server.send_message(msg)
                
            logging.info(f"Notification email sent to {recipient_email}")
            return True
        except Exception as e:
            logging.error(f"Failed to send email: {e}")
            return False
