from app.models.waitlist import Waitlist
from sqlmodel import select
from app.schemas.waitlist import WaitlistCreate
from sqlalchemy.ext.asyncio.session import AsyncSession
from fastapi import HTTPException


async def create_waitlist_repo(waitlist: WaitlistCreate, db: AsyncSession) -> Waitlist:
    """
    :param db:
    :param waitlist:
    """
    stmt = Waitlist(**waitlist.model_dump())
    waitlist = await get_user_waitlist_repo(db, str(waitlist.email))
    if waitlist is None:
        try:
            db.add(stmt)
            await db.commit()
            await db.refresh(stmt)
            return stmt
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error Creating Waitlist. Full Error code: {e}")
    else:
        raise HTTPException(status_code=404, detail="User Already Registered to Wait List")

async def get_user_waitlist_repo(db: AsyncSession, email: str) -> Waitlist:
    """
    :param db:
    :param email:
    :return:
    """
    stmt = select(Waitlist).where(Waitlist.email == email)
    try:
        payload = await db.execute(stmt)
        result = payload.scalars().first()
        print(f"Testing {result} ")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error Getting User Waitlist. Full Error code: {e}")