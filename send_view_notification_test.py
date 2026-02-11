
import sys
import os
import asyncio
from app.dependencies.email_service import EmailService

# Add app to path
sys.path.append(os.getcwd())

async def send_test_email():
    email_to = "adoxop1@gmail.com"
    subject = "Test: Someone viewed your confession"
    template_name = "confess_viewed_notification.html"

    # Mock data for the template
    template_body = {
        "name": "Test Sender",
        "recipient_name": "Test Recipient",
        "confess_type": "dinner_date",
        "slug": "test-slug-123",
        "project_name": "CONFESS",
        "project_url": "https://confess.com.ng"
    }

    print(f"Sending test view notification to {email_to}...")
    try:
        # We can use the internal helper for direct sending without background tasks context
        EmailService._send_email_async(
            subject=subject,
            email_to=email_to,
            template_body=template_body,
            template_name=template_name
        )
        print(f"Email sent successfully to {email_to}")
    except Exception as e:
        print(f"Failed to send email to {email_to}: {e}")

if __name__ == "__main__":
    # Since _send_email_async is synchronous (despite the name, it calls Mailjet sync),
    # we can run it directly. If it were async, we'd need asyncio.run
    # Checking previous files, it seems _send_email_async is actually synchronous in the provided code
    # (it uses mailjet client which is typically sync unless configured otherwise,
    # and the method definition def _send_email_async(...) lacks 'async').

    # However, to be safe and consistent with previous scripts:
    asyncio.run(send_test_email())
