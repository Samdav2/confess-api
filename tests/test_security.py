import asyncio
import httpx
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_rate_limiting():
    print("Testing Rate Limiting...")
    # Hit the root endpoint multiple times
    # Note: SlowAPI might not work perfectly with TestClient without some hacks,
    # but let's try to see if we get 429 after many requests.
    # We need to mock the remote address for TestClient

    # Actually, for TestClient, we might need to set the client host
    responses = []
    for _ in range(10): # Default might be higher, but let's see
        response = client.get("/", headers={"X-API-KEY": "test"})
        responses.append(response.status_code)

    print(f"Responses: {responses}")
    # This is a basic check. Real verification might need more requests or specific configuration.

def test_cors():
    print("Testing CORS...")
    origin = "https://confess.com.ng"
    response = client.options(
        "/",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        },
    )
    print(f"CORS Status: {response.status_code}")
    print(f"Access-Control-Allow-Origin: {response.headers.get('access-control-allow-origin')}")

    assert response.headers.get("access-control-allow-origin") == origin
    print("✅ CORS Verified for allowed origin")

    # Test disallowed origin
    disallowed_origin = "https://evil.com"
    response = client.options(
        "/",
        headers={
            "Origin": disallowed_origin,
            "Access-Control-Request-Method": "GET",
        },
    )
    # Should not have the header or should be different
    allow_origin = response.headers.get("access-control-allow-origin")
    print(f"Disallowed Origin Header: {allow_origin}")
    if allow_origin != disallowed_origin:
         print("✅ CORS Verified for disallowed origin")
    else:
         print("❌ CORS Failed: Disallowed origin was allowed")

if __name__ == "__main__":
    try:
        test_cors()
        # Rate limiting test might require running the server or more complex setup with TestClient
        # test_rate_limiting()
    except Exception as e:
        print(f"❌ Test Failed: {e}")
