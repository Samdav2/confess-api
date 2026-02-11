
import sys
import asyncio
import os
from uuid import UUID

sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi import BackgroundTasks

from app.config.settings import settings
from app.service.confess_form import ConfessFormService
from app.models.confess_form import DeliveryMethod, ConfessType

# Mock BackgroundTasks to execute immediately
class MockBackgroundTasks(BackgroundTasks):
    def add_task(self, func, *args, **kwargs):
        print(f"Executing background task: {func.__name__}")
        try:
            func(*args, **kwargs)
        except Exception as e:
            print(f"Background task failed: {e}")

async def test_auto_notification(phone_number):
    database_url = str(settings.DATABASE_URL)
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        service = ConfessFormService(session)

        user_id = UUID("7af11c88-9b31-4e7b-a0e0-ed1b02d7e334")

        from app.schemas.confess_form import ConfessFormCreate
        confess_data = ConfessFormCreate(
            delivery=DeliveryMethod.PHONE,
            phone=phone_number,
            email=None,
            confess_type=ConfessType.DINNER_DATE,
            tone="Friendly",
            message="Hello, this is an automatic test message from Confess App.",
            sender_name="AutoTester",
            recipient_name="AutoRecipient",
            anonymous=False
        )

        try:
            print("Triggering create_confess_form (should auto-send)...")
            bg_tasks = MockBackgroundTasks()

            # This should now trigger send_confess_form internally
            result = await service.create_confess_form(user_id, confess_data, bg_tasks)
            print(f"Service Result: {result}")

            # Since create_confess_form generates its own slug, we need to extract it for cleanup
            test_slug = result.slug

        except Exception as e:
            print(f"Error during creation/send: {e}")
            import traceback
            traceback.print_exc()
            test_slug = None
        finally:
            # Cleanup
            if test_slug:
                print(f"Cleaning up test form {test_slug}...")
                created_form = await service.repository.get_by_slug(test_slug)
                if created_form:
                    await session.delete(created_form)
                    await session.commit()
                print("Cleanup complete.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/test_auto_notif.py <phone_number>")
        sys.exit(1)

    asyncio.run(test_auto_notification(sys.argv[1]))
