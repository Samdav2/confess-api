import asyncio
from app.db.sessions import engine
from app.models.feedback import Feedback
from sqlmodel import SQLModel

async def recreate_table():
    async with engine.begin() as conn:
        print("Dropping feedbacks table...")
        await conn.run_sync(Feedback.__table__.drop, checkfirst=True)
        print("Creating feedbacks table...")
        await conn.run_sync(SQLModel.metadata.create_all)
        print("Table recreated.")

if __name__ == "__main__":
    asyncio.run(recreate_table())
