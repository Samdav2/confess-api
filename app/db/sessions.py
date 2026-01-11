from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from app.config.settings import settings

engine = create_async_engine(
    url=settings.DATABASE_URL,
    echo=True,
    pool_size=10,
    max_overflow=20,
)

async def get_session() -> AsyncSession:
    async with AsyncSession(engine) as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)