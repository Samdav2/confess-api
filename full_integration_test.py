import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from app.service.confess_form import ConfessFormService
from app.schemas.confess_form import ConfessFormCreate, ConfessType, DeliveryMethod
from app.models.user import User
from sqlmodel import select
from dotenv import load_dotenv
import logging

# Configure logging to stdout
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Also enable SQLAlchemy logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

load_dotenv()

async def main():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(database_url)

    async with AsyncSession(engine) as session:
        # 1. Get a test user
        statement = select(User).limit(1)
        result = await session.exec(statement)
        user = result.first()

        if not user:
            print("❌ No user found in database to test with.")
            # Create a mock user if needed? Let's assume there is one.
            return

        print(f"Testing with user: {user.email}")

        service = ConfessFormService(session)

        # 2. Create a confession
        # Use a safe confession type to avoid safety blocks
        confess_data = ConfessFormCreate(
            confess_type=ConfessType.DINNER_DATE,
            tone="Appreciative",
            message="You are a great friend.",
            delivery=DeliveryMethod.EMAIL,
            email="test@example.com",
            recipient_name="Test Recipient"
        )

        print("\n--- Starting create_confess_form ---")
        try:
            response = await service.create_confess_form(user.id, confess_data)
            print("\n✅ SUCCESS! Response:")
            print(f"AI Message: {response.ai_message}")

            # Check if it's the fallback
            fallback_start = "Sometimes words fail to capture what's in the heart"
            if response.ai_message and response.ai_message.startswith(fallback_start):
                print("\n⚠️ WARNING: The response IS the fallback message!")
            else:
                print("\n✨ Looks like a real AI message!")

        except Exception as e:
            print(f"\n❌ FAILED with error: {e}")
            logger.exception("Traceback:")

if __name__ == "__main__":
    asyncio.run(main())
