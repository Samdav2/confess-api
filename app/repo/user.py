from typing import Union
from fastapi import HTTPException
from fastapi.logger import logger
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.user import User
from app.schemas.user import UserCreate, UserRead
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select


async def create_user(new_user: UserCreate, db: AsyncSession) -> UserRead:
    """
    Most efficient: Let the database handle uniqueness with constraints.
    No need to check if user exists first - just try to create and catch errors.
    """
    try:
        user = User(**new_user.model_dump())
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return UserRead.model_validate(user)

    except IntegrityError as e:
        await db.rollback()
        error_msg = str(e.orig).lower() if hasattr(e, 'orig') else str(e).lower()

        # Debug logging to identify the exact constraint violation
        logger.error(f"IntegrityError during user creation: {error_msg}")
        logger.error(f"Full error: {e}")

        if "email" in error_msg:
            raise HTTPException(
                status_code=409,
                detail="A user with this email already exists"
            )
        elif "referral_code" in error_msg:
            raise HTTPException(
                status_code=409,
                detail="Referral code conflict. Please try again"
            )
        else:
            # Log the unexpected constraint for debugging
            logger.error(f"Unknown IntegrityError constraint: {error_msg}")
            raise HTTPException(
                status_code=409,
                detail=f"User already exists (constraint: {error_msg[:100]})"
            )

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Database error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error occurred")

    except Exception as e:
        await db.rollback()
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

async def get_user_by_email(email: str, db: AsyncSession) -> Union[UserRead, None]:
    """
    :param email:
    :param db:
    :return:
    """
    if email:
        stmt = select(User).where(User.email == email)
        result = await db.exec(stmt)
        user = result.first()
        print(f"user: {user}")
        if not user:
            return None
        return UserRead.model_validate(user)
    else:
        raise HTTPException(status_code=404, detail=" Email not provided or Invalid")
