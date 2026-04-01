import requests
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notifications")

class NotificationService:
    """Enterprise Alerting Service for Webhooks (Slack/Discord/Custom)."""
    
    def __init__(self):
        self.webhook_url = os.getenv("WEBHOOK_URL")

    def send_alert(self, title: str, message: str, severity: str = "Medium"):
        """Sends a JSON payload to the configured webhook."""
        if not self.webhook_url:
            logger.warning(f"⚠️ Webhook URL not configured. Mock Alert: [{severity}] {title}: {message}")
            return False
            
        payload = {
            "text": f"🚨 *{title}* (Severity: {severity})\n{message}",
            "severity": severity,
            "timestamp": logger.info("Dispatching real alert...")
        }
        
        try:
            response = requests.post(self.webhook_url, json=payload, timeout=5)
            response.raise_for_status()
            logger.info("✅ Alert sent successfully via Webhook.")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to dispatch alert: {e}")
            return False

if __name__ == "__main__":
    notifier = NotificationService()
    notifier.send_alert("Test Hazard", "Oil spill detected in Slot 4")
