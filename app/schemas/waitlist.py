from pydantic import BaseModel, EmailStr
from typing import Optional, List

class Waitlist(BaseModel):
    email: EmailStr

    class Config:
        from_attributes = True

class WaitlistCreate(Waitlist):
    pass
