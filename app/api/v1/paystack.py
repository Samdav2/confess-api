from fastapi import APIRouter, Depends, Request, Header, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.sessions import get_session
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.schemas.paystack import (
    PaystackInitializeRequest,
    PaystackInitializeResponse,
    PaystackVerifyResponse,
    PaymentResponse
)
from app.service.paystack_service import paystack_service
from typing import List

router = APIRouter()

@router.post("/initialize", response_model=PaystackInitializeResponse)
async def initialize_payment(
    request: PaystackInitializeRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    return await paystack_service.initialize_transaction(
        session=session,
        user_id=current_user.id,
        email=request.email,
        amount=request.amount,
        callback_url=request.callback_url
    )

@router.get("/verify/{reference}", response_model=PaystackVerifyResponse)
async def verify_payment(
    reference: str,
    session: AsyncSession = Depends(get_session)
):
    return await paystack_service.verify_transaction(session, reference)

@router.get("/callback", response_model=PaystackVerifyResponse)
async def paystack_callback(
    reference: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Handle Paystack redirect callback.
    Paystack appends ?reference=... to the callback URL.
    """
    return await paystack_service.verify_transaction(session, reference)

@router.post("/webhook")
async def paystack_webhook(
    request: Request,
    x_paystack_signature: str = Header(None),
    session: AsyncSession = Depends(get_session)
):
    if not x_paystack_signature:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing signature")

    body = await request.body()
    return await paystack_service.handle_webhook(session, body, x_paystack_signature)

@router.get("/transactions", response_model=List[PaymentResponse])
async def list_transactions(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    return await paystack_service.list_transactions(session, current_user.id)
