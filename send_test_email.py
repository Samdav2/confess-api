import sys
import os
from app.dependencies.email_service import EmailService

# Add app to path
sys.path.append(os.getcwd())

def send_test_emails():
    recipients = [
        "adoxop1@gmail.com",
        "amiolademilade@gmail.com"
    ]

    subject = "Test Email from CONFESS"
    template_name = "user_welcome.html"
    template_body = {
        "title": "Welcome to Confess!",
        "name": "Test User"
    }

    for email_to in recipients:
        print(f"Sending test email to {email_to}...")
        try:
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
    send_test_emails()
