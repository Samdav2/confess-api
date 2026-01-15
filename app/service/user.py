from app.repo.user import create_user
from app.schemas.user import UserCreate
from sqlmodel.ext.asyncio.session import AsyncSession
from bcrypt import hashpw, gensalt
from app.dependencies.referral_code import generate_referral_code

async def create_user_service(new_user: UserCreate, db: AsyncSession):
    """
    Python function at the service level to create new user object
    :param new_user:
    :param db:
    :return:
    """
    user_referral_code = await generate_referral_code(new_user.username)
    hash_pass = hashpw(new_user.password.encode("utf-8"), gensalt()).decode("utf-8")
    new_user.password = hash_pass
    new_user.referral_code = user_referral_code
    user = await create_user(new_user, db)
    return user