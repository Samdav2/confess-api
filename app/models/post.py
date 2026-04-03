from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, String, Text
from sqlmodel import SQLModel, Field, Relationship
from uuid import UUID, uuid4
from typing import Optional, List


class Post(SQLModel, table=True):
    __tablename__ = "posts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str = Field(sa_column=Column(String(255), nullable=False, index=True))
    slug: str = Field(sa_column=Column(String(255), nullable=False, unique=True, index=True))
    content: str = Field(sa_column=Column(Text, nullable=False))
    summary: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))

    # SEO Fields
    meta_title: Optional[str] = Field(default=None, sa_column=Column(String(255), nullable=True))
    meta_description: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    meta_keywords: Optional[str] = Field(default=None, sa_column=Column(String(255), nullable=True))
    canonical_url: Optional[str] = Field(default=None, sa_column=Column(String(255), nullable=True))

    featured_image: Optional[str] = Field(default=None, sa_column=Column(String(500), nullable=True))

    is_published: bool = Field(default=False, index=True)
    published_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True),
        default=None
    )

    author_id: UUID = Field(foreign_key="admins.id", nullable=False, index=True)

    category: Optional[str] = Field(default=None, index=True)
    tags: Optional[str] = Field(default=None) # Comma separated tags

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    author: Optional["Admin"] = Relationship()
    comments: List["Comment"] = Relationship(back_populates="post", sa_relationship_kwargs={"cascade": "all, delete-orphan"})


class Comment(SQLModel, table=True):
    __tablename__ = "comments"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    post_id: UUID = Field(foreign_key="posts.id", nullable=False, index=True)
    user_id: Optional[UUID] = Field(default=None, foreign_key="users.id", nullable=True, index=True)

    # Guest info (used if user_id is null)
    name: Optional[str] = Field(default=None, sa_column=Column(String(255), nullable=True))
    email: Optional[str] = Field(default=None, sa_column=Column(String(255), nullable=True))

    content: str = Field(sa_column=Column(Text, nullable=False))
    is_approved: bool = Field(default=False, index=True)

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    post: Optional[Post] = Relationship(back_populates="comments")
    user: Optional["User"] = Relationship(back_populates="comments")
