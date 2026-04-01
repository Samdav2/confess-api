import asyncio
from sqlmodel import create_engine, select
from sqlalchemy import inspect
from app.config.settings import settings
import os

async def check_schema():
    engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))
    inspector = inspect(engine)
    columns = inspector.get_columns('celebration_pages')
    print("Columns in celebration_pages:")
    for col in columns:
        print(f"- {col['name']}")

if __name__ == "__main__":
    asyncio.run(check_schema())
