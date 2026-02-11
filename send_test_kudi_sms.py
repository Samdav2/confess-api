
import sys
import os
import logging

# Add app to path
sys.path.append(os.getcwd())

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.service.kudi_sms_service import kudi_sms_service

def send_test_sms():
    # Replace with a valid phone number for testing
    recipient = os.getenv("TEST_PHONE_NUMBER", "2348030000000")
    message = "Test SMS from CONFESS API via Kudi"

    print(f"Sending test SMS to {recipient}...")
    try:
        response = kudi_sms_service.send_sms(
            to=recipient,
            message=message
        )
        print(f"SMS sent result: {response}")
    except Exception as e:
        print(f"Failed to send SMS to {recipient}: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        os.environ["TEST_PHONE_NUMBER"] = sys.argv[1]
    send_test_sms()
