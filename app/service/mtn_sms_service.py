import requests
import time
import uuid
from typing import Optional, Dict, Any
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)

class MTNSMSService:
    def __init__(self):
        self.base_url = settings.MTN_API_BASE_URL.rstrip('/')
        self.client_id = settings.MTN_CLIENT_ID
        self.client_secret = settings.MTN_CLIENT_SECRET
        self.sender_id = settings.MTN_SENDER_ID
        self._access_token: Optional[str] = None
        self._token_expiry: float = 0

    def _get_access_token(self) -> str:
        """
        Get valid access token, refreshing if necessary.
        Uses Client Credentials flow.
        """
        if self._access_token and time.time() < self._token_expiry:
            return self._access_token

        try:
            # Using the URL that successfully returns a token
            url = f"{self.base_url}/oauth/client_credential/accesstoken"
            params = {
                "grant_type": "client_credentials"
            }

            response = requests.post(
                url,
                params=params,
                auth=(self.client_id, self.client_secret)
            )
            response.raise_for_status()
            data = response.json()

            self._access_token = data.get("access_token")
            expires_in = data.get("expires_in", 3599)
            self._token_expiry = time.time() + float(expires_in) - 60

            return self._access_token

        except Exception as e:
            logger.error(f"Failed to obtain MTN access token: {e}")
            raise

    def send_sms(self, to: str, message: str) -> Dict[str, Any]:
        """
        Send SMS using MTN API v1.
        """
        try:
            token = self._get_access_token()
            # v3 Endpoint definition from swagger
            url = f"{self.base_url}/v3/sms/messages"

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            # v1 Payload Structure (from definition SendSMS)
            payload = {
                "to": [to],
                "body": message,
                "from": self.sender_id,
                "clientId": settings.PROJECT_NAME
            }

            response = requests.post(url, json=payload, headers=headers)
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                logger.error(f"MTN SMS API Error: {response.text}")
                raise

            return response.json()

        except Exception as e:
            logger.error(f"Failed to send MTN SMS: {e}")
            raise

# Singleton instance
mtn_sms_service = MTNSMSService()
