from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

# Link Schemas
class AnonymousLinkCreateRequest(BaseModel):
    header_text: str = "Send me a message 💌"
    theme_color: str = "#8b5cf6"

class AnonymousLinkResponse(BaseModel):
    id: UUID
    slug: str
    header_text: str
    theme_color: str
    is_active: bool
    expires_at: datetime
    created_at: datetime

# Message Schemas
class AnonymousMessageCreateRequest(BaseModel):
    type: str = "text"  # text or voice
    content: str
    hint: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class AnonymousMessageResponse(BaseModel):
    id: UUID
    type: str
    content: str
    hint: Optional[str] = None  # Only if unlocked or user is owner and unlocked
    is_hint_unlocked: bool
    is_sender_clue_unlocked: bool
    created_at: datetime
    # Clues (only if unlocked)
    ip_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    user_agent: Optional[str] = None
    network_info: Optional[str] = None

class UnlockRequest(BaseModel):
    # Just a placeholder for now, maybe used for validation later
    pass
