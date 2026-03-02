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
    DashboardStatsResponse
)
from app.service.admin import (
    create_admin,
    login_admin,
    reset_admin_password,
    get_dashboard_metrics
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
