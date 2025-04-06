
import requests
import time
from twilio.rest import Client
from config import get_required_env
import logging

logger = logging.getLogger(__name__)

def send_sms_notification(message):
    account_sid = get_required_env("TWILIO_ACCOUNT_SID")
    auth_token = get_required_env("TWILIO_AUTH_TOKEN")
    from_number = get_required_env("TWILIO_FROM_NUMBER")
    to_number = get_required_env("TWILIO_TO_NUMBER")
    
    try:
        client = Client(account_sid, auth_token)
        client.messages.create(
            body=message,
            from_=from_number,
            to=to_number
        )
        logger.info("SMS notification sent successfully")
    except Exception as e:
        logger.error(f"Failed to send SMS: {e}")

def monitor_scraper():
    check_interval = 300  # 5 minutes
    health_endpoint = "http://0.0.0.0:5000/health"
    
    while True:
        try:
            response = requests.get(health_endpoint)
            if response.status_code != 200:
                send_sms_notification(
                    f"Scraper Alert: Health check failed with status {response.status_code}"
                )
        except Exception as e:
            send_sms_notification(
                f"Scraper Alert: Scraper is down - {str(e)}"
            )
        
        time.sleep(check_interval)

if __name__ == "__main__":
    monitor_scraper()
