from fastapi import APIRouter, Depends, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID

from app.db.sessions import get_session
from app.dependencies.auth import get_current_admin
from app.models.admin import Admin
from app.schemas.post import (
    PostCreate,
    PostUpdate,
    PostResponse,
    PaginatedPostsResponse
)
from app.service.post_service import (
    create_post,
    get_all_posts_admin,
    get_post_by_id,
    update_post,
    delete_post
)

router = APIRouter()


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED, summary="[Admin] Create a new post")
@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED, summary="[Admin] Create a new post", include_in_schema=False)
async def admin_create_post(
    request: PostCreate,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_session)
):
    """Create a new post with SEO fields."""
    return await create_post(db=db, post_in=request, author_id=current_admin.id)


@router.get("", response_model=PaginatedPostsResponse, summary="[Admin] List all posts")
@router.get("/", response_model=PaginatedPostsResponse, summary="[Admin] List all posts", include_in_schema=False)
async def admin_get_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_session)
):
    """List posts for admin with pagination."""
    data = await get_all_posts_admin(db=db, skip=skip, limit=limit)
    return data


@router.get("/{post_id}", response_model=PostResponse, summary="[Admin] Get post detail")
async def admin_get_post(
    post_id: UUID,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_session)
):
    """Retrieve post details by ID."""
    return await get_post_by_id(db=db, post_id=post_id)


@router.patch("/{post_id}", response_model=PostResponse, summary="[Admin] Update post")
async def admin_update_post(
    post_id: UUID,
    request: PostUpdate,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_session)
):
    """Update post fields."""
    return await update_post(db=db, post_id=post_id, post_update=request)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT, summary="[Admin] Delete post")
async def admin_delete_post(
    post_id: UUID,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_session)
):
    """Delete post."""
    await delete_post(db=db, post_id=post_id)
    return None
