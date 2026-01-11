import asyncio
import logging
from app.dependencies.email_service import EmailService
from app.config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_mailjet():
    print(f"Testing Mailjet integration...")
    print(f"API Key: {settings.MAILJET_API_KEY[:4]}***")
    print(f"Secret Key: {settings.MAILJET_SECRET_KEY[:4]}***")
    print(f"Sender: {settings.MAIL_FROM}")

    # Test data
    test_email = "techio.com.ng@gmail.com" # Replace with a real email if needed, or check logs
    subject = "Mailjet Verification Test"
    template_body = {"title": "Mailjet Test", "name": "Tester"}
    template_name = "waitlist.html"

    try:
        # Calling the internal async method directly to bypass BackgroundTasks for this test
        EmailService._send_email_async(
            subject=subject,
            email_to=test_email,
            template_body=template_body,
            template_name=template_name
        )
        print("Test function executed. Check logs for Mailjet response.")
    except Exception as e:
        print(f"Test failed with exception: {e}")

if __name__ == "__main__":
    asyncio.run(verify_mailjet())
