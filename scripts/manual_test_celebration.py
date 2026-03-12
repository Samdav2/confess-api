import asyncio
from uuid import uuid4
from sqlalchemy import select
from app.db.sessions import get_session
from app.models.celebration import CelebrationPage, OccasionType, MusicType, PaymentStatus
from app.service.celebration_service import CelebrationService
from app.schemas.celebration import CelebrationPageCreate
from app.models.user import User

async def manual_test():
    print("Starting manual test...")
    async for session in get_session():
        service = CelebrationService(session)

        # 1. Get a user
        statement = select(User)
        result = await session.exec(statement)
        user = result.scalars().first()

        if not user:
            print("No user found, creating a test user...")
            user = User(
                username="testuser",
                email=f"test-{uuid4().hex[:8]}@example.com",
                password="hashed_password",
                referral_code=f"REF-{uuid4().hex[:8]}"
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

        print(f"Using user: {user.email} (ID: {user.id})")

        # 2. Check slug availability
        slug = f"test-slug-{uuid4().hex[:4]}"
        available = await service.check_slug_availability(slug)
        print(f"Slug '{slug}' available: {available}")

        # 3. Create a celebration page
        create_data = CelebrationPageCreate(
            slug=slug,
            recipient_name="John Doe",
            occasion_type=OccasionType.BIRTHDAY,
            images=["img1.jpg", "img2.jpg", "img3.jpg", "img4.jpg"], # 4 images -> 1500
            music_type=MusicType.APP_MUSIC, # 200
            music_url="song1.mp3"
        )

        print("Creating celebration page...")
        celebration = await service.create_celebration_page(user.id, create_data)
        print(f"Created celebration ID: {celebration.id}")
        print(f"Total Price: {celebration.total_price}") # Expected: 1500 + 200 = 1700

        # 4. Get by slug
        fetched = await service.get_celebration_by_slug(slug)
        print(f"Fetched celebration recipient: {fetched.recipient_name}")

        # 5. Initialize payment (mocking)
        print("Initializing payment...")
        # Note: This will actually call Paystack API if settings are valid.
        # For testing, we might just want to see if it generates the payload correctly.
        try:
            pay_resp = await service.initialize_payment(celebration.id, user.id, user.email)
            print(f"Payment initialized. Reference: {pay_resp.reference}")
        except Exception as e:
            print(f"Payment initialization failed (expected if keys missing): {e}")

        print("Test completed successfully!")
        break

if __name__ == "__main__":
    asyncio.run(manual_test())
