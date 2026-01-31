import os
import asyncio
from app.service.groq_service import GroqService
from dotenv import load_dotenv
import logging

# Configure logging to see service logs
logging.basicConfig(level=logging.INFO)

load_dotenv()

async def main():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("API Key missing")
        return

    print(f"API Key prefix: {api_key[:5]}...")

    service = GroqService(api_key)
    try:
        print("Attempting to generate content...")
        response = await service.generate_confession_message(
            tone="humorous",
            confess_type="mild crush",
            recipient_name="Dave"
        )
        print(f"\nResponse:\n{response}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
