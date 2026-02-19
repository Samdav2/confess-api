import asyncio
from app.dependencies.email_service import email_service
from app.config.settings import settings
from app.db.sessions import AsyncSession, engine
from app.repo.waitlist import get_all_waitlist_repo
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    print("Starting bulk 'Website Launch' notification sending...")

    async with AsyncSession(engine) as session:
        try:
            # Fetch all users from waitlist
            users = await get_all_waitlist_repo(session)
            print(f"Found {len(users)} users on the waitlist.")

            if not users:
                print("No users found on the waitlist. Exiting.")
                return

            sent_count = 0
            for user in users:
                target_email = user.email
                print(f"Sending launch notification to {target_email}...")

                # Context for the template
                template_body = {
                    "title": "We are LIVE: Confess.com.ng is back!",
                    "name": "User", # Or user.name if available, model only has email
                    "current_year": 2026,
                    "site_url": settings.FRONTEND_URL,
                    "cta_link": f"{settings.FRONTEND_URL}",
                    "cta_text": "Visit Website Now"
                }

                try:
                    # Send email
                    email_service._send_email_async(
                        subject="Good News: Confess.com.ng is now LIVE!",
                        email_to=target_email,
                        template_body=template_body,
                        template_name="website_live.html"
                    )
                    sent_count += 1
                except Exception as e:
                    print(f"Error sending email to {target_email}: {e}")

                # Small delay to avoid hitting rate limits too hard if many users
                await asyncio.sleep(0.5)

            print(f"Bulk sending complete. Sent {sent_count} emails.")

        except Exception as e:
            print(f"An error occurred during bulk sending: {e}")

if __name__ == "__main__":
    asyncio.run(main())
