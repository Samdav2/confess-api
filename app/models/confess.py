from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship

class AnonymousLink(SQLModel, table=True):
    __tablename__ = "anonymous_links"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    slug: str = Field(unique=True, index=True)
    header_text: str = Field(default="Send me a message 💌")
    theme_color: str = Field(default="#8b5cf6")
    text_color: str = Field(default="#ffffff")
    emoji: str = Field(default="❤️")
    is_active: bool = Field(default=True)
    is_extended: bool = Field(default=False)
    expires_at: datetime = Field(nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    messages: List["AnonymousMessage"] = Relationship(back_populates="link")
    user: Optional["User"] = Relationship(back_populates="anonymous_links")

class AnonymousMessage(SQLModel, table=True):
    __tablename__ = "anonymous_messages"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    link_id: UUID = Field(foreign_key="anonymous_links.id", index=True)
    type: str = Field(default="text")  # text or voice
    content: str = Field(nullable=False)  # text content or file path
    hint: Optional[str] = Field(default=None)

    # Location/Device info (for clues)
    ip_address: Optional[str] = Field(default=None)
    latitude: Optional[float] = Field(default=None)
    longitude: Optional[float] = Field(default=None)
    user_agent: Optional[str] = Field(default=None)
    network_info: Optional[str] = Field(default=None) # ISP or City/Region info

    # Unlock status
    is_hint_unlocked: bool = Field(default=False)
    is_sender_clue_unlocked: bool = Field(default=False)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    link: Optional[AnonymousLink] = Relationship(back_populates="messages")
