from google import genai
import os
import asyncio

async def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("API Key missing")
        return

    client = genai.Client(api_key=api_key)
    try:
        print("Attempting to generate content...")
        response = await client.aio.models.generate_content(
            model='gemini-2.0-flash',
            contents='Hello, world!'
        )
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
