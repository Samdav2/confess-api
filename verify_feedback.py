import asyncio
import httpx
from uuid import uuid4

async def test_feedback_endpoint():
    url = "http://localhost:8000/api/v1/feedback"
    data = {
        "name": "Test User",
        "message": "This is a test feedback message.",
        "rating": 5
    }

    async with httpx.AsyncClient() as client:
        # Since I can't start the server here easily without blocking, this test assumes
        # the server is running or I mock it.
        # But wait, I can try to start it in background, or just use `TestClient` from fastapi.
        pass

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_feedback():
    response = client.post(
        "/api/v1/feedback",
        json={
            "name": "Test User",
            "message": "This is a test feedback message.",
            "rating": 5
        }
    )
    print(response.status_code)
    print(response.json())
    assert response.status_code == 200
    assert response.json()["name"] == "Test User"
    assert response.json()["rating"] == 5
    print("Test passed!")

if __name__ == "__main__":
    test_create_feedback()
