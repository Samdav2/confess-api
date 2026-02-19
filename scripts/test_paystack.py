import asyncio
import sys
import os
from sqlalchemy import select

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.sessions import get_session
from app.models.user import User
from app.service.paystack_service import paystack_service
from app.config.settings import settings

async def main():
    print("Testing Paystack Integration...")

    if not settings.PAYSTACK_SECRET_KEY:
        print("Error: PAYSTACK_SECRET_KEY not set in environment/settings.")
        return

    async for session in get_session():
        # Get a test user
        result = await session.exec(select(User).limit(1))
        user = result.first()

        if not user:
            print("Error: No users found in database to test with.")
            return

        print(f"Using user: {user.email}")

        # 1. Initialize Transaction
        print("\n1. Initializing Transaction...")
        try:
            init_response = await paystack_service.initialize_transaction(
                session=session,
                user_id=user.id,
                email=user.email,
                amount=100.00,  # 100 Naira
                callback_url="http://localhost:8000/api/v1/paystack/verify"
            )
            print("Initialization Successful:")
            print(f"  Authorization URL: {init_response.authorization_url}")
            print(f"  Access Code: {init_response.access_code}")
            print(f"  Reference: {init_response.reference}")

            reference = init_response.reference
        except Exception as e:
            print(f"Initialization Failed: {e}")
            return

        # 2. Verify Transaction (Initially Pending)
        print(f"\n2. Verifying Transaction ({reference})...")
        try:
            verify_response = await paystack_service.verify_transaction(
                session=session,
                reference=reference
            )
            print("Verification Successful:")
            print(f"  Status: {verify_response.status}")
            print(f"  Message: {verify_response.message}")
        except Exception as e:
             print(f"Verification Failed: {e}")

        # 3. List Transactions
        print(f"\n3. Listing Transactions for user {user.id}...")
        try:
            transactions = await paystack_service.list_transactions(session, user.id)
            print(f"Found {len(transactions)} transactions.")
            for tx in transactions[:5]:
                print(f"  - {tx.reference}: {tx.amount} {tx.currency} ({tx.status})")
        except Exception as e:
            print(f"Listing Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
