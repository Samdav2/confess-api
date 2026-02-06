import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

async def fix_schema():
    print(f"Connecting to database...")
    engine = create_async_engine(DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        print("Adding missing columns to confess_forms...")

        # Add date_value
        try:
            await conn.execute(text("ALTER TABLE confess_forms ADD COLUMN IF NOT EXISTS date_value TIMESTAMP WITH TIME ZONE;"))
            print("Added date_value column.")
        except Exception as e:
            print(f"Error adding date_value: {e}")

        # Add allow_recipient_to_choose
        try:
            await conn.execute(text("ALTER TABLE confess_forms ADD COLUMN IF NOT EXISTS allow_recipient_to_choose BOOLEAN NOT NULL DEFAULT FALSE;"))
            print("Added allow_recipient_to_choose column.")
        except Exception as e:
            print(f"Error adding allow_recipient_to_choose: {e}")

        # Add date_answer
        try:
            await conn.execute(text("ALTER TABLE confess_forms ADD COLUMN IF NOT EXISTS date_answer BOOLEAN;"))
            print("Added date_answer column.")
        except Exception as e:
            print(f"Error adding date_answer: {e}")

        # Add date_tpe
        try:
            await conn.execute(text("ALTER TABLE confess_forms ADD COLUMN IF NOT EXISTS date_tpe JSON;"))
            print("Added date_tpe column.")
        except Exception as e:
            print(f"Error adding date_tpe: {e}")

        # Add recipient_date_proposal
        try:
             await conn.execute(text("ALTER TABLE confess_forms ADD COLUMN IF NOT EXISTS recipient_date_proposal TIMESTAMP WITH TIME ZONE;"))
             print("Added recipient_date_proposal column.")
        except Exception as e:
            print(f"Error adding recipient_date_proposal: {e}")

        # Add paid
        try:
             await conn.execute(text("ALTER TABLE confess_forms ADD COLUMN IF NOT EXISTS paid BOOLEAN DEFAULT TRUE;"))
             print("Added paid column.")
        except Exception as e:
            print(f"Error adding paid: {e}")

    await engine.dispose()
    print("Schema update complete.")

if __name__ == "__main__":
    asyncio.run(fix_schema())
