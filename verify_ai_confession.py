import asyncio
import os
from uuid import uuid4
from app.db.sessions import init_db, get_session
from app.service.confess_form import ConfessFormService
from app.schemas.confess_form import ConfessFormCreate, ConfessType, DeliveryMethod
from app.models.confess_form import ConfessForm
from app.models.user import User  # Assuming User model exists
from sqlmodel import select
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock user ID for testing
TEST_USER_ID = uuid4()

async def create_test_user(session):
    # Check if user exists or create one
    # For simplicity, we might just insert a user if foreign key constraint exists
    # Or we can disable FK checks, but better to be correct.
    # Let's try to find a user or create one.
    # Since I don't know the User model details fully, I'll try to insert a minimal user.
    # Actually, let's just use a random UUID and hope FK doesn't fail or we can insert a user.
    # Looking at ConfessForm model: user_id: UUID = Field(foreign_key="users.id", nullable=False)
    # So we need a user.

    # Let's try to get the first user from DB
    result = await session.exec(select(User))
    user = result.first()
    if user:
        return user.id

    # If no user, create one (this might fail if User model has required fields I don't know)
    # I'll try to skip user creation and hope there is one, or I'll fail.
    print("No user found in DB. Cannot proceed without a user.")
    return None

async def main():
    print("Initializing DB...")
    await init_db()

    async for session in get_session():
        print("Session created.")

        # Get a user ID
        user_id = await create_test_user(session)
        if not user_id:
            print("Skipping test due to missing user.")
            return

        print(f"Using User ID: {user_id}")

        service = ConfessFormService(session)

        # Create Confession Form
        print("Creating Confession Form...")
        confess_data = ConfessFormCreate(
            confess_type=ConfessType.DINNER_DATE,
            tone="Romantic and poetic",
            message="I love you",
            recipient_name="Alice",
            delivery=DeliveryMethod.EMAIL,
            email="alice@example.com"
        )

        try:
            created_form = await service.create_confess_form(user_id, confess_data)
            print(f"Confession Form Created: {created_form.id}")
            print(f"Slug: {created_form.slug}")

            # Verify AI Message
            if created_form.ai_message:
                print(f"AI Message Generated: {created_form.ai_message}")
            else:
                print("AI Message NOT Generated (might be async or failed).")

            # Fetch by ID to verify persistence
            fetched_form = await service.get_confess_form(created_form.id, user_id)
            print(f"Fetched AI Message: {fetched_form.ai_message}")

            if fetched_form.ai_message:
                print("SUCCESS: AI Message persisted and retrieved.")
            else:
                print("FAILURE: AI Message lost.")

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

        break # Exit after one session usage

if __name__ == "__main__":
    asyncio.run(main())
