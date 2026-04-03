from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from uuid import UUID
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, status
import re

from app.models.post import Post
from app.schemas.post import PostCreate, PostUpdate


def generate_slug(title: str) -> str:
    """Generate a URL-friendly slug from a title."""
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug


async def create_post(db: AsyncSession, post_in: PostCreate, author_id: UUID) -> Post:
    """Create a new post with SEO fields and slug generation."""
    # Check if slug already exists
    statement = select(Post).where(Post.slug == post_in.slug)
    result = await db.execute(statement)
    if result.scalar_one_or_none():
        # If slug exists, append a timestamp or handle collision
        post_in.slug = f"{post_in.slug}-{int(datetime.now().timestamp())}"

    post = Post(
        **post_in.model_dump(),
        author_id=author_id
    )

    if post.is_published and not post.published_at:
        post.published_at = datetime.now(timezone.utc)

    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post


async def get_all_posts_admin(db: AsyncSession, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
    """Get all posts for admin with pagination."""
    total_statement = select(func.count()).select_from(Post)
    total_result = await db.execute(total_statement)
    total = total_result.scalar() or 0

    statement = select(Post).order_by(Post.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(statement)
    items = result.scalars().all()

    return {"total": total, "items": items}


async def get_post_by_id(db: AsyncSession, post_id: UUID) -> Post:
    """Retrieve a post by its ID."""
    statement = select(Post).where(Post.id == post_id)
    result = await db.execute(statement)
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    return post


async def update_post(db: AsyncSession, post_id: UUID, post_update: PostUpdate) -> Post:
    """Update an existing post."""
    post = await get_post_by_id(db, post_id)

    update_data = post_update.model_dump(exclude_unset=True)

    # Handle published_at logic
    if "is_published" in update_data:
        if update_data["is_published"] and not post.is_published and not post.published_at:
            update_data["published_at"] = datetime.now(timezone.utc)
        elif not update_data["is_published"]:
             update_data["published_at"] = None

    for key, value in update_data.items():
        setattr(post, key, value)

    post.updated_at = datetime.now(timezone.utc)

    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post


async def delete_post(db: AsyncSession, post_id: UUID) -> None:
    """Delete a post."""
    post = await get_post_by_id(db, post_id)
    await db.delete(post)
    await db.commit()


# --- Public Services ---

async def get_published_posts(db: AsyncSession, skip: int = 0, limit: int = 10) -> Dict[str, Any]:
    """Get only published posts for the public blog."""
    total_statement = select(func.count()).select_from(Post).where(Post.is_published == True)
    total_result = await db.execute(total_statement)
    total = total_result.scalar() or 0

    statement = (
        select(Post)
        .where(Post.is_published == True)
        .order_by(Post.published_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(statement)
    items = result.scalars().all()

    return {"total": total, "items": items}


async def get_post_by_slug_public(db: AsyncSession, slug: str) -> Post:
    """Retrieve a published post by its slug for public view."""
    statement = select(Post).where(Post.slug == slug, Post.is_published == True)
    result = await db.execute(statement)
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    return post


# --- Comment Services ---

from app.models.post import Comment
from app.schemas.post import CommentCreate
from app.models.user import User

async def create_comment(
    db: AsyncSession,
    post_id: UUID,
    comment_in: CommentCreate,
    user: Optional[User] = None
) -> Comment:
    """Create a comment for a post. Supports both authenticated and guest users."""
    # Verify post exists and is published
    post_statement = select(Post).where(Post.id == post_id, Post.is_published == True)
    post_result = await db.execute(post_statement)
    if not post_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    if not user:
        if not comment_in.name or not comment_in.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Name and email are required for guest comments"
            )
        comment = Comment(
            post_id=post_id,
            content=comment_in.content,
            name=comment_in.name,
            email=comment_in.email,
            is_approved=False # Requires moderation
        )
    else:
        comment = Comment(
            post_id=post_id,
            user_id=user.id,
            content=comment_in.content,
            name=user.username,
            email=user.email,
            is_approved=True # Auto-approve for logged in users
        )

    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment


async def get_post_comments(db: AsyncSession, post_id: UUID) -> List[Comment]:
    """Retrieve approved comments for a post."""
    statement = (
        select(Comment)
        .where(Comment.post_id == post_id, Comment.is_approved == True)
        .order_by(Comment.created_at.desc())
    )
    result = await db.execute(statement)
    return result.scalars().all()
