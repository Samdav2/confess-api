import asyncio
from sqlalchemy import text
from app.db.sessions import engine

async def run_migration():
    async with engine.begin() as conn:
        print("🔌 Connected to DB")
        try:
            print("🔄 Adding is_extended column to anonymous_links...")
            await conn.execute(text("ALTER TABLE anonymous_links ADD COLUMN IF NOT EXISTS is_extended BOOLEAN DEFAULT FALSE;"))
            print("✅ Column added successfully to anonymous_links.")

            print("🔄 Adding columns to anonymous_messages...")
            await conn.execute(text("ALTER TABLE anonymous_messages ADD COLUMN IF NOT EXISTS is_hint_unlocked BOOLEAN DEFAULT FALSE;"))
            await conn.execute(text("ALTER TABLE anonymous_messages ADD COLUMN IF NOT EXISTS is_sender_clue_unlocked BOOLEAN DEFAULT FALSE;"))

            await conn.execute(text("ALTER TABLE anonymous_messages ADD COLUMN IF NOT EXISTS ip_address VARCHAR;"))
            await conn.execute(text("ALTER TABLE anonymous_messages ADD COLUMN IF NOT EXISTS user_agent VARCHAR;"))
            await conn.execute(text("ALTER TABLE anonymous_messages ADD COLUMN IF NOT EXISTS network_info VARCHAR;"))
            await conn.execute(text("ALTER TABLE anonymous_messages ADD COLUMN IF NOT EXISTS latitude FLOAT;"))
            await conn.execute(text("ALTER TABLE anonymous_messages ADD COLUMN IF NOT EXISTS longitude FLOAT;"))

            print("✅ Columns added successfully to anonymous_messages.")
        except Exception as e:
            print(f"❌ Failed to add column: {e}")

if __name__ == "__main__":
    asyncio.run(run_migration())
