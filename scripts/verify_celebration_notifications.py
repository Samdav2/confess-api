import asyncio
from uuid import uuid4
from unittest.mock import MagicMock
from fastapi import BackgroundTasks
from app.service.celebration_service import CelebrationService
from app.schemas.celebration import CelebrationPageCreate, DeliveryMethod, OccasionType, MusicType
from sqlmodel.ext.asyncio.session import AsyncSession

async def test_celebration_logic():
    # Mock session and repository
    mock_session = MagicMock(spec=AsyncSession)
    service = CelebrationService(mock_session)
    service.repository = MagicMock()
    service.repository.get_by_slug = MagicMock(return_value=asyncio.Future())
    service.repository.get_by_slug.return_value.set_result(None)

    service.repository.create = MagicMock(return_value=asyncio.Future())

    # Test data
    user_id = uuid4()
    data = CelebrationPageCreate(
        slug="test-celebration",
        recipient_name="John Doe",
        occasion_type=OccasionType.BIRTHDAY,
        delivery=DeliveryMethod.EMAIL,
        email="john@example.com",
        images=["img1.jpg"]
    )

    # Mock background tasks
    bg_tasks = MagicMock(spec=BackgroundTasks)

    # Mock return celebration
    from app.models.celebration import CelebrationPage
    created_celebration = CelebrationPage(
        **data.model_dump(),
        id=uuid4(),
        created_by=user_id,
        total_price=1000.0,
        payment_status="pending",
        user=MagicMock(username="sender")
    )
    service.repository.create.return_value.set_result(created_celebration)

    print("Testing celebration creation with email...")
    try:
        await service.create_celebration_page(user_id, data, bg_tasks)
        print("✓ Creation successful")
    except Exception as e:
        print(f"✗ Creation failed: {e}")
        return

    # Verify that notification was triggered (indirectly via background tasks)
    print("Verifying notification trigger...")
    if bg_tasks.add_task.called:
        print("✓ Notification triggered in background tasks")
    else:
        print("✗ Notification NOT triggered")

if __name__ == "__main__":
    asyncio.run(test_celebration_logic())
