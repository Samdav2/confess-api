from pydantic import BaseModel, EmailStr, Field, validator
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from enum import Enum


class ConfessType(str, Enum):
    DINNER_DATE = "dinner_date"
    ANONYMOUS = "anonymous"
    APPRECIATION = "appreciation"


class DeliveryMethod(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"


class ConfessFormCreate(BaseModel):
    confess_type: ConfessType = Field(default=ConfessType.DINNER_DATE)
    tone: str = Field(..., min_length=1, max_length=50)
    message: str = Field(..., min_length=1, max_length=5000)
    anonymous: bool = Field(default=False)
    card_design: int = Field(default=0, ge=0)
    delivery: DeliveryMethod = Field(default=DeliveryMethod.EMAIL)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

    sender_name: Optional[str] = Field(None, max_length=100)
    recipient_name: Optional[str] = Field(None, max_length=100)

    date_value: Optional[datetime] = None
    date_answer: Optional[bool] = None
    date_tpe: Optional[List[str]] = None

    @validator('email')
    def validate_email_delivery(cls, v, values):
        if values.get('delivery') == DeliveryMethod.EMAIL and not v:
            raise ValueError('Email is required when delivery method is EMAIL')
        return v

    @validator('phone')
    def validate_phone_delivery(cls, v, values):
        if values.get('delivery') == DeliveryMethod.WHATSAPP and not v:
            raise ValueError('Phone is required when delivery method is WHATSAPP')
        return v

    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.startswith('+'):
            raise ValueError('Phone number must include country code (e.g., +234...)')
        return v


class ConfessFormUpdate(BaseModel):
    confess_type: Optional[ConfessType] = None
    tone: Optional[str] = Field(None, min_length=1, max_length=50)
    message: Optional[str] = Field(None, min_length=1, max_length=5000)
    anonymous: Optional[bool] = None
    card_design: Optional[int] = Field(None, ge=0)
    delivery: Optional[DeliveryMethod] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

    sender_name: Optional[str] = Field(None, max_length=100)
    recipient_name: Optional[str] = Field(None, max_length=100)



    date_value: Optional[datetime] = None
    date_answer: Optional[bool] = None
    date_tpe: Optional[List[str]] = None


class ConfessFormResponse(BaseModel):
    id: UUID
    user_id: UUID
    confess_type: ConfessType
    tone: str
    message: str
    anonymous: bool
    card_design: int
    delivery: DeliveryMethod
    email: Optional[str]
    phone: Optional[str]

    sender_name: Optional[str]
    recipient_name: Optional[str]
    date_value: Optional[datetime] = None
    date_answer: Optional[bool] = None
    date_tpe: Optional[List[str]] = None
    ai_message: Optional[str] = None
    slug: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConfessFormListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ConfessFormResponse]


class ConfessFormAnswer(BaseModel):
    date_answer: bool
