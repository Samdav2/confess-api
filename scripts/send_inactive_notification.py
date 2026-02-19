import asyncio
from app.dependencies.email_service import email_service
from app.config.settings import settings
from fastapi import BackgroundTasks
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Target email from user request
    target_email = "adoxop1@gmail.com"

    background_tasks = BackgroundTasks()

    print(f"Sending test 'Website Inactive' notification to {target_email}...")

    # Context for the template
    template_body = {
        "title": "Website Update: Confess.com.ng",
        "name": "User",
        "current_year": 2026,
        "site_url": settings.FRONTEND_URL,
        "cta_link": f"{settings.FRONTEND_URL}/confess",
        "cta_text": "Start Confessing Now"
    }

    try:
        # We call the internal helper directly since we are in a script and don't want to use FastAPI's BackgroundTasks lifecycle
        email_service._send_email_async(
            subject="Important Update: Website Status & Confessions",
            email_to=target_email,
            template_body=template_body,
            template_name="website_inactive.html"
        )
        print("Done. Please check your inbox.")
    except Exception as e:
        print(f"Error sending email: {e}")

if __name__ == "__main__":
    asyncio.run(main())
