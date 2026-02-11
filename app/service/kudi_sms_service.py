
import requests
from typing import Optional, Dict, Any
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)

class KudiSMSService:
    def __init__(self):
        self.base_url = "https://my.kudisms.net/api/sms"
        self.api_key = settings.KUDI_API_KEY
        self.sender_id = settings.KUDI_SENDER_ID

    def send_sms(self, to: str, message: str) -> Dict[str, Any]:
        """
        Send SMS using Kudi SMS API.
        """
        try:
            # Using JSON payload as per documentation
            headers = {
                'Content-Type': 'application/json'
            }

            payload = {
                "token": self.api_key,
                "senderID": self.sender_id,
                "recipients": to,
                "message": message,
                "gateway": "2"
            }

            response = requests.post(self.base_url, json=payload, headers=headers)

            try:
                response.raise_for_status()
                data = response.json()

                # Check for API specific error codes (even if HTTP 200)
                # Kudi returns "status": "success" or "error_code": "000"
                if data.get("error_code") != "000" and data.get("status") != "success":
                     logger.error(f"Kudi SMS API logic error: {data}")
                     # Decide if we want to raise an exception for logic errors
                     # For now, just logging it.

                return data

            except requests.exceptions.HTTPError:
                logger.error(f"Kudi SMS API HTTP Error: {response.text}")
                raise

        except Exception as e:
            logger.error(f"Failed to send Kudi SMS: {e}")
            raise

# Singleton instance
kudi_sms_service = KudiSMSService()
