import asyncio
import uuid
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.sessions import engine
from app.service.confess_service import confess_service
from app.schemas.confess import AnonymousLinkCreateRequest
from app.models.user import User

async def debug_create_link():
    async with AsyncSession(engine) as session:
        print("🔌 Connected to DB")

        # 1. Get or Create a User
        # We need a valid user ID. Let's try to find one or create a dummy one if possible,
        # but creating a user might require more deps.
        # Let's try to fetch the user created by the test script if possible, or just any user.
        # Actually, the test script created a user, let's try to find it by email pattern or just get first user.

        from sqlmodel import select
        result = await session.exec(select(User).limit(1))
        user = result.first()

        if not user:
            print("❌ No user found in DB. Cannot test link creation.")
            # Verify if we can create one directly
            try:
                new_user = User(
                    email=f"debug_{uuid.uuid4()}@example.com",
                    username=f"debug_{uuid.uuid4().hex[:8]}",
                    password="hashedpassword",
                    referral_code=f"REF-{uuid.uuid4().hex[:6]}"
                )
                session.add(new_user)
                await session.commit()
                await session.refresh(new_user)
                user = new_user
                print(f"✅ Created debug user: {user.id}")
            except Exception as e:
                print(f"❌ Failed to create debug user: {e}")
                return

        print(f"👤 Using user: {user.id}")

        # 2. Try to create link
        request = AnonymousLinkCreateRequest(
            header_text="Debug Header",
            theme_color="#000000"
        )

        print("🚀 Attempting to create link...")
        try:
            link = await confess_service.create_link(session, user.id, request)
            print(f"✅ Link created successfully! ID: {link.id}, Slug: {link.slug}")
        except Exception as e:
            print(f"❌ Error creating link: {e}")
            import traceback
            traceback.print_exc()
            return

        # 3. Try to submit message
        from app.schemas.confess import AnonymousMessageCreateRequest
        msg_request = AnonymousMessageCreateRequest(
            content="Debug Message",
            hint="Debug Hint"
        )
        print("🚀 Attempting to submit message...")
        try:
            message = await confess_service.submit_message(
                session=session,
                slug=link.slug,
                request=msg_request,
                ip_address="127.0.0.1",
                user_agent="Mozilla/5.0 (Test)"
            )
            print(f"✅ Message submitted successfully! ID: {message.id}")
        except Exception as e:
            print(f"❌ Error submitting message: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_create_link())
