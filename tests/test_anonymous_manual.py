import asyncio
import httpx
import random
import string

# Configuration
BASE_URL = "http://127.0.0.1:8000"
API_V1_STR = "/api/v1"
API_KEY = "90b4a188604c9ba1e16d251a9f9c194e012da74a3b482b4f340f64141e0af72a"

def generate_random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

async def test_anonymous_flow():
    headers = {"X-API-KEY": API_KEY}
    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=60.0) as client:
        print("🚀 Starting Anonymous Endpoint Tests...")

        # 0. Check connectivity
        try:
            resp = await client.get("/")
            print(f"✅ Server is up: {resp.status_code}")
        except Exception as e:
            print(f"❌ Server unreachable: {e}")
            return

        # 1. Register a new user
        print("\nDOING: Registering new user...")
        username = f"testuser_{generate_random_string()}"
        email = f"{username}@example.com"
        password = "TestPassword123!"

        register_data = {
            "username": username,
            "email": email,
            "password": password,
            "phone_number": f"080{generate_random_string(8)}" # Mock phone number
        }

        response = await client.post(f"{API_V1_STR}/user/create", json=register_data)
        if response.status_code != 200:
            print(f"❌ Registration failed: {response.text}")
            return

        user_data = response.json()
        print(f"✅ User registered: {user_data.get('username')}")

        # 2. Login to get token
        print("\nDOING: Logging in...")
        login_data = {
            "email": email,
            "password": password
        }
        response = await client.post(f"{API_V1_STR}/auth/login", json=login_data)
        if response.status_code != 200:
            print(f"❌ Login failed: {response.text}")
            return

        token_data = response.json()
        access_token = token_data['access_token']
        headers = {"Authorization": f"Bearer {access_token}"}
        print("✅ Login successful, token received.")

        # 3. Create Anonymous Link
        print("\nDOING: Creating Anonymous Link...")
        link_data = {
            "username": username,
            "theme": "default",
            "redirect_url": "https://google.com"
        }
        response = await client.post(f"{API_V1_STR}/anonymous/links", json=link_data, headers=headers)
        if response.status_code != 200:
            print(f"❌ Create Link failed: {response.text}")
            return

        link_response = response.json()
        slug = link_response['slug']
        print(f"✅ Link created. Slug: {slug}")

        # 4. Get Link by Slug (Public)
        print(f"\nDOING: Fetching link details for slug: {slug}...")
        response = await client.get(f"{API_V1_STR}/anonymous/links/{slug}")
        if response.status_code != 200:
            print(f"❌ Get Link failed: {response.text}")
            return
        print("✅ Link details fetched successfully.")

        # 5. Submit a Message (Public)
        print("\nDOING: Submitting an anonymous message...")
        message_data = {
            "content": "This is a secret message!",
            "sender_name": "Secret Admirer", # might be optional
            "hint": "I sit next to you."
        }
        # Note: Confess endpoints might expect latitude/longitude if your schema requires it,
        # but let's try with minimal data first.
        # Looking at schema might be needed if this fails.

        # Let's add extra data based on common patterns or just try/fail
        response = await client.post(f"{API_V1_STR}/anonymous/links/{slug}/messages", json=message_data)
        if response.status_code != 200:
             print(f"❌ Submit Message failed: {response.text}")
             # Warning: schema might require lat/long.
             # Let's retry with more data if 422
             if response.status_code == 422:
                 print("   -> Retrying with simpler payload or checking params...")
             return

        message_response = response.json()
        message_id = message_response['id']
        print(f"✅ Message submitted. ID: {message_id}")

        # 6. Retrieve Messages (Protected)
        print("\nDOING: Retrieving messages as owner...")
        response = await client.get(f"{API_V1_STR}/anonymous/links/{slug}/messages", headers=headers)
        if response.status_code != 200:
            print(f"❌ Get Messages failed: {response.text}")
            return

        messages = response.json()
        print(f"✅ Messages retrieved. Count: {len(messages)}")

        # Verify content masking
        first_msg = messages[0]
        if "Locked" in str(first_msg.get('hint', '')):
             print("✅ Hint is correctly locked/masked.")
        else:
             print(f"⚠️ Hint might be unlocked or format changed: {first_msg.get('hint')}")

        # 7. Start/Unlock Hint (Simulated)
        # This usually requires payment, but we can check if the endpoint exists and returns 402 or similar
        # Or if we can call it.
        print(f"\nDOING: Attempting to unlock hint for message {message_id}...")
        # Note: You likely need a payment flow, but let's see what the endpoint does.
        # It calls `unlock_hint`.
        response = await client.post(f"{API_V1_STR}/anonymous/messages/{message_id}/unlock-hint", headers=headers)
        if response.status_code == 200:
             print("✅ Hint unlocked (maybe valid for MVP/Test logic).")
        else:
             print(f"ℹ️ Unlock Hint response: {response.status_code} - {response.text}")

        # 8. Extend Link Expiry
        print("\nDOING: Extending link expiry...")
        response = await client.post(f"{API_V1_STR}/anonymous/links/{slug}/extend", headers=headers)
        if response.status_code != 200:
            print(f"❌ Extend Link failed: {response.text}")
        else:
            print("✅ Link expiry extended.")

        print("\n🎉 All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_anonymous_flow())
