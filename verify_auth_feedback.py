import asyncio
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.sessions import engine
from app.models.user import User
from app.dependencies.auth import create_access_token
from app.dependencies.referral_code import generate_referral_code
from app.service.auth import hash_password
from app.main import app
from sqlmodel import select

async def get_or_create_user(session: AsyncSession):
    # Check for existing test user
    result = await session.execute(select(User).where(User.email == "test@example.com"))
    user = result.scalar_one_or_none()

    if not user:
        print("Creating test user...")
        # Need to generate referral code async
        ref_code = await generate_referral_code("testuser")
        user = User(
            email="test@example.com",
            username="testuser",
            password=hash_password("password123"),
            email_verified=True,
            referral_code=ref_code,
            referred_by=""
        )
        session.add(user)
        try:
            await session.commit()
            await session.refresh(user)
        except Exception:
            await session.rollback()
            # Try fetching again in case of race condition or error
            result = await session.execute(select(User).where(User.email == "test@example.com"))
            user = result.scalar_one()

    return user

async def main():
    # Use the same engine for setup and app execution (simulated)
    async with AsyncSession(engine) as session:
        user = await get_or_create_user(session)
        token = create_access_token(user_id=str(user.id), email=user.email)

    headers = {"Authorization": f"Bearer {token}"}
    print(f"Testing with user: {user.email}")

    # Use httpx.AsyncClient with the app
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:

        # 1. Test Success Case
        response = await client.post(
            "/api/v1/feedback",
            json={
                "message": "This is an authenticated feedback message.",
                "rating": 4
            },
            headers=headers
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

        assert response.status_code == 200
        assert response.json()["name"] == "testuser"
        assert response.json()["rating"] == 4

        # 2. Test Unauthorized Case
        response_unauth = await client.post(
            "/api/v1/feedback",
            json={
                "message": "This should fail.",
                "rating": 1
            }
        )
        print(f"Unauthorized Status Code: {response_unauth.status_code}")
        assert response_unauth.status_code == 401

    print("Test passed!")

if __name__ == "__main__":
    asyncio.run(main())
