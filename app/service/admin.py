from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, func
from fastapi import HTTPException, status
from typing import Tuple, Dict, Any

from app.models.admin import Admin
from app.models.user import User
from app.models.confess import AnonymousLink, AnonymousMessage
from app.models.confess_form import ConfessForm
from app.schemas.admin import AdminCreate
from passlib.context import CryptContext
from app.dependencies.auth import create_access_token, get_token_expiry_seconds

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def create_admin(db: AsyncSession, admin_in: AdminCreate) -> Admin:
    statement = select(Admin).where(Admin.email == admin_in.email)
    result = await db.execute(statement)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin with this email already exists"
        )

    admin = Admin(
        email=admin_in.email,
        username=admin_in.username,
        password=get_password_hash(admin_in.password),
        is_super_admin=admin_in.is_super_admin
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return admin

async def login_admin(db: AsyncSession, email: str, password: str) -> Tuple[Admin, str, int]:
    statement = select(Admin).where(Admin.email == email)
    result = await db.execute(statement)
    admin = result.scalar_one_or_none()

    if not admin or not verify_password(password, admin.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        user_id=str(admin.id),
        email=admin.email
    )
    expires_in = get_token_expiry_seconds()

    return admin, access_token, expires_in

async def reset_admin_password(db: AsyncSession, email: str, new_password: str) -> Admin:
    statement = select(Admin).where(Admin.email == email)
    result = await db.execute(statement)
    admin = result.scalar_one_or_none()

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )

    admin.password = get_password_hash(new_password)
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return admin

async def get_dashboard_metrics(db: AsyncSession) -> Dict[str, int]:
    try:
        total_users = await db.execute(select(func.count()).select_from(User))
        total_confess_forms = await db.execute(select(func.count()).select_from(ConfessForm))
        total_anonymous_links = await db.execute(select(func.count()).select_from(AnonymousLink))
        total_messages = await db.execute(select(func.count()).select_from(AnonymousMessage))

        return {
            "total_users": total_users.scalar() or 0,
            "total_confess_forms": total_confess_forms.scalar() or 0,
            "total_anonymous_links": total_anonymous_links.scalar() or 0,
            "total_messages": total_messages.scalar() or 0
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard metrics: {str(e)}"
        )

async def get_all_users_admin(db: AsyncSession, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
    total = await db.execute(select(func.count()).select_from(User))
    statement = select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(statement)
    return {"total": total.scalar() or 0, "items": result.scalars().all()}

async def get_all_confess_forms_admin(db: AsyncSession, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
    total = await db.execute(select(func.count()).select_from(ConfessForm))
    statement = select(ConfessForm).order_by(ConfessForm.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(statement)
    return {"total": total.scalar() or 0, "items": result.scalars().all()}

async def get_all_anonymous_links_admin(db: AsyncSession, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
    total = await db.execute(select(func.count()).select_from(AnonymousLink))
    statement = select(AnonymousLink).order_by(AnonymousLink.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(statement)
    return {"total": total.scalar() or 0, "items": result.scalars().all()}

async def get_all_anonymous_messages_admin(db: AsyncSession, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
    total = await db.execute(select(func.count()).select_from(AnonymousMessage))
    statement = select(AnonymousMessage).order_by(AnonymousMessage.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(statement)
    return {"total": total.scalar() or 0, "items": result.scalars().all()}
