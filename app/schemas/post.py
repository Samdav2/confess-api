from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class PostBase(BaseModel):
    title: str
    slug: str
    content: str
    summary: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    canonical_url: Optional[str] = None
    featured_image: Optional[str] = None
    is_published: bool = False
    category: Optional[str] = None
    tags: Optional[str] = None


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    canonical_url: Optional[str] = None
    featured_image: Optional[str] = None
    is_published: Optional[bool] = None
    published_at: Optional[datetime] = None
    category: Optional[str] = None
    tags: Optional[str] = None


class PostResponse(PostBase):
    id: UUID
    author_id: UUID
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedPostsResponse(BaseModel):
    total: int
    items: List[PostResponse]


class CommentBase(BaseModel):
    content: str


class CommentCreate(CommentBase):
    name: Optional[str] = None
    email: Optional[str] = None


class CommentResponse(CommentBase):
    id: UUID
    post_id: UUID
    user_id: Optional[UUID] = None
    name: Optional[str] = None
    email: Optional[str] = None
    is_approved: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CommentPublicResponse(BaseModel):
    id: UUID
    name: Optional[str] = None # Will be user.username or guest name
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
