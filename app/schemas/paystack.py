from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class PaystackInitializeRequest(BaseModel):
    email: EmailStr
    amount: float
    callback_url: Optional[str] = None
    metadata: Optional[dict] = None

class PaystackInitializeResponse(BaseModel):
    authorization_url: str
    access_code: str
    reference: str

class PaystackVerifyResponse(BaseModel):
    payment_status: str          # success | failed | abandoned
    is_paid: bool
    message: str
    reference: Optional[str] = None
    amount: Optional[float] = None   # in main currency unit (e.g. Naira)

class PaymentResponse(BaseModel):
    id: UUID
    reference: str
    amount: float
    currency: str
    status: str
    channel: Optional[str]
    paid_at: Optional[datetime]
    created_at: datetime
