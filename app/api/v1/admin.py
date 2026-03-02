from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Dict, Any

from app.db.sessions import get_session
from app.dependencies.auth import get_current_admin
from app.schemas.auth import LoginResponse
from app.schemas.admin import (
    AdminCreate,
    AdminLogin,
    AdminResponse,
    AdminPasswordReset,
    AdminLoginResponse,
    DashboardStatsResponse,
    PaginatedUsersResponse,
    PaginatedConfessFormsResponse,
    PaginatedAnonymousLinksResponse,
    PaginatedAnonymousMessagesResponse
)
from app.service.admin import (
    create_admin,
    login_admin,
    reset_admin_password,
    get_dashboard_metrics,
    get_all_users_admin,
    get_all_confess_forms_admin,
    get_all_anonymous_links_admin,
    get_all_anonymous_messages_admin
)
from app.models.admin import Admin

router = APIRouter()

@router.post("/create", response_model=AdminResponse, summary="Create a new admin account")
async def create_new_admin(
    request: AdminCreate,
    db: AsyncSession = Depends(get_session)
):
    admin = await create_admin(db=db, admin_in=request)
    return admin

@router.post("/login", response_model=AdminLoginResponse, summary="Login admin account")
async def login(
    request: AdminLogin,
    db: AsyncSession = Depends(get_session)
):
    admin, access_token, expires_in = await login_admin(
        db=db,
        email=request.email,
        password=request.password
    )
    return AdminLoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        admin=AdminResponse.model_validate(admin)
    )

@router.post("/reset-password", response_model=AdminResponse, summary="Reset admin password")
async def reset_password(
    request: AdminPasswordReset,
    db: AsyncSession = Depends(get_session)
):
    return await reset_admin_password(
        db=db,
        email=request.email,
        new_password=request.new_password
    )

@router.get("/dashboard-stats", response_model=DashboardStatsResponse, summary="[Admin] Get Dashboard Summary")
async def dashboard_stats(
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_session)
):
    """
    Get backend summary totals strictly for Admin dashboard users.
    """
    metrics = await get_dashboard_metrics(db=db)
    return DashboardStatsResponse(**metrics)

@router.get("/users", response_model=PaginatedUsersResponse, summary="[Admin] Get paginated users")
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_session)
):
    """Get all standard users."""
    data = await get_all_users_admin(db=db, skip=skip, limit=limit)
    return data

@router.get("/confess-forms", response_model=PaginatedConfessFormsResponse, summary="[Admin] Get paginated confess forms")
async def get_confess_forms(
    skip: int = 0,
    limit: int = 100,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_session)
):
    """Get all confess forms."""
    data = await get_all_confess_forms_admin(db=db, skip=skip, limit=limit)
    return data

@router.get("/anonymous-links", response_model=PaginatedAnonymousLinksResponse, summary="[Admin] Get paginated anonymous links")
async def get_anonymous_links(
    skip: int = 0,
    limit: int = 100,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_session)
):
    """Get all anonymous links."""
    data = await get_all_anonymous_links_admin(db=db, skip=skip, limit=limit)
    return data

@router.get("/anonymous-messages", response_model=PaginatedAnonymousMessagesResponse, summary="[Admin] Get paginated anonymous messages")
async def get_anonymous_messages(
    skip: int = 0,
    limit: int = 100,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_session)
):
    """Get all anonymous messages."""
    data = await get_all_anonymous_messages_admin(db=db, skip=skip, limit=limit)
    return data
