from fastapi import APIRouter, Depends, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional
from app.db.sessions import get_session
from app.dependencies.auth import get_current_user
from app.schemas.confess_form import (
    ConfessFormCreate,
    ConfessFormUpdate,
    ConfessFormResponse,
    ConfessFormListResponse
)
from app.service.confess_form import ConfessFormService

router = APIRouter(
    prefix="/api/v1/confess-forms",
)


async def get_confess_service(session: AsyncSession = Depends(get_session)) -> ConfessFormService:
    """Dependency to get confess form service"""
    return ConfessFormService(session)


@router.post(
    "/",
    response_model=ConfessFormResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new confess form"
)
async def create_confess_form(
        confess_data: ConfessFormCreate,
        current_user_id: UUID = Depends(get_current_user),
        service: ConfessFormService = Depends(get_confess_service)
):
    """
    Create a new confess form.

    - **confess_type**: Type of confession (dinner_date, anonymous, appreciation)
    - **tone**: Tone of the message
    - **message**: The confession message
    - **anonymous**: Whether the confession is anonymous
    - **card_design**: Design ID for the card
    - **delivery**: Delivery method (email or whatsapp)
    - **email**: Email address (required if delivery is email)
    - **phone**: Phone number (required if delivery is whatsapp)
    - **name**: Recipient name (optional)
    """
    return await service.create_confess_form(current_user_id, confess_data)


@router.post(
    "/{slug}/send",
    status_code=status.HTTP_200_OK,
    summary="Send confess form notification"
)
async def send_confess_form(
        slug: str,
        background_tasks: BackgroundTasks,
        service: ConfessFormService = Depends(get_confess_service)
):
    """
    Trigger the sending of a confess form via Email or WhatsApp.

    - **slug**: The unique slug of the confess form
    """
    return await service.send_confess_form(slug, background_tasks)


@router.get(
    "/{confess_id}",
    response_model=ConfessFormResponse,
    summary="Get a confess form by ID"
)
async def get_confess_form(
        confess_id: UUID,
        current_user_id: UUID = Depends(get_current_user),
        service: ConfessFormService = Depends(get_confess_service)
):
    """
    Get a specific confess form by ID.

    Users can only access their own confess forms.
    """
    return await service.get_confess_form(confess_id, current_user_id)


@router.get(
    "/",
    response_model=ConfessFormListResponse,
    summary="Get user's confess forms"
)
async def get_user_confess_forms(
        page: int = Query(default=1, ge=1, description="Page number"),
        page_size: int = Query(default=10, ge=1, le=100, description="Items per page"),
        confess_type: Optional[str] = Query(default=None, description="Filter by confess type"),
        current_user_id: UUID = Depends(get_current_user),
        service: ConfessFormService = Depends(get_confess_service)
):
    """
    Get all confess forms for the current user with pagination.

    - **page**: Page number (starts at 1)
    - **page_size**: Number of items per page (max 100)
    - **confess_type**: Optional filter by confession type
    """
    return await service.get_user_confess_forms(
        user_id=current_user_id,
        page=page,
        page_size=page_size,
        confess_type=confess_type
    )


@router.put(
    "/{confess_id}",
    response_model=ConfessFormResponse,
    summary="Update a confess form"
)
async def update_confess_form(
        confess_id: UUID,
        update_data: ConfessFormUpdate,
        current_user_id: UUID = Depends(get_current_user),
        service: ConfessFormService = Depends(get_confess_service)
):
    """
    Update a confess form.

    Users can only update their own confess forms.
    Only provided fields will be updated.
    """
    return await service.update_confess_form(confess_id, current_user_id, update_data)


@router.delete(
    "/{confess_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a confess form"
)
async def delete_confess_form(
        confess_id: UUID,
        current_user_id: UUID = Depends(get_current_user),
        service: ConfessFormService = Depends(get_confess_service)
):
    """
    Delete a confess form.

    Users can only delete their own confess forms.
    """
    await service.delete_confess_form(confess_id, current_user_id)
    return None


# Optional: Admin endpoint to get all confess forms
@router.get(
    "/admin/all",
    response_model=ConfessFormListResponse,
    summary="[Admin] Get all confess forms",
    tags=["Admin"]
)
async def get_all_confess_forms_admin(
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=10, ge=1, le=100),
        confess_type: Optional[str] = Query(default=None),
        delivery: Optional[str] = Query(default=None),
        # Add your admin auth dependency here
        # current_admin: Admin = Depends(get_current_admin),
        service: ConfessFormService = Depends(get_confess_service)
):
    """
    [Admin only] Get all confess forms with optional filters.
    """
    skip = (page - 1) * page_size
    confess_forms, total = await service.repository.get_all(
        skip=skip,
        limit=page_size,
        confess_type=confess_type,
        delivery=delivery
    )

    return ConfessFormListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[ConfessFormResponse.model_validate(cf) for cf in confess_forms]
    )
