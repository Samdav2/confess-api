from fastapi import APIRouter, Depends, Query, status
from typing import Optional, List
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID

from app.db.sessions import get_session
from app.dependencies.auth import oauth2_scheme, verify_token
from app.models.user import User
from app.schemas.post import (
    PostResponse,
    PaginatedPostsResponse,
    CommentCreate,
    CommentPublicResponse
)
from app.service.post_service import (
    get_published_posts,
    get_post_by_slug_public,
    create_comment,
    get_post_comments
)
from sqlmodel import select

router = APIRouter()

async def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_session)
) -> Optional[User]:
    """Optional dependency to get the current user if token is provided."""
    if not token:
        return None
    try:
        token_data = verify_token(token)
        user_id = UUID(token_data.user_id)
        statement = select(User).where(User.id == user_id)
        result = await db.execute(statement)
        return result.scalar_one_or_none()
    except Exception:
        return None


@router.get("/", response_model=PaginatedPostsResponse, summary="List all published posts")
async def list_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_session)
):
    """List published posts for the public blog."""
    return await get_published_posts(db=db, skip=skip, limit=limit)


@router.get("/{slug}", response_model=PostResponse, summary="Get published post by slug")
async def get_post(
    slug: str,
    db: AsyncSession = Depends(get_session)
):
    """Retrieve a published post by slug."""
    return await get_post_by_slug_public(db=db, slug=slug)


@router.post("/{post_id}/comments", response_model=CommentPublicResponse, status_code=status.HTTP_201_CREATED, summary="Add a comment to a post")
async def add_post_comment(
    post_id: UUID,
    request: CommentCreate,
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_session)
):
    """
    Add a comment.
    If logged in, user info is used and comment is auto-approved.
    If not logged in, name and email must be provided and comment requires moderation.
    """
    comment = await create_comment(
        db=db,
        post_id=post_id,
        comment_in=request,
        user=user
    )
    # Map to public response
    return CommentPublicResponse(
        id=comment.id,
        name=comment.name,
        content=comment.content,
        created_at=comment.created_at
    )


@router.get("/{post_id}/comments", response_model=List[CommentPublicResponse], summary="List approved comments for a post")
async def list_post_comments(
    post_id: UUID,
    db: AsyncSession = Depends(get_session)
):
    """List all approved comments for a specific post."""
    comments = await get_post_comments(db=db, post_id=post_id)
    return [
        CommentPublicResponse(
            id=c.id,
            name=c.name,
            content=c.content,
            created_at=c.created_at
        ) for c in comments
    ]
