import asyncio
from app.db.sessions import init_db
import app.models  # Ensure models are registered

async def main():
    print("Creating tables...")
    await init_db()
    print("Tables created.")

if __name__ == "__main__":
    asyncio.run(main())
