import hmac
import hashlib
import httpx
from fastapi import HTTPException, status
from app.config.settings import settings
from app.models.payment import Payment
from app.schemas.paystack import PaystackInitializeResponse, PaystackVerifyResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from datetime import datetime, timezone
import json

class PaystackService:
    BASE_URL = "https://api.paystack.co"

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }

    async def initialize_transaction(
        self, session: AsyncSession, user_id: str, email: str, amount: float, callback_url: str = None, confess_form_id: str = None
    ) -> PaystackInitializeResponse:
        url = f"{self.BASE_URL}/transaction/initialize"
        # Paystack amount is in kobo
        amount_kobo = int(amount * 100)

        metadata = {"user_id": str(user_id)}
        if confess_form_id:
            metadata["confess_form_id"] = str(confess_form_id)

        payload = {
            "email": email,
            "amount": amount_kobo,
            "callback_url": callback_url,
            "metadata": json.dumps(metadata)
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self.headers, json=payload)

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Paystack initialization failed: {response.text}"
            )

        data = response.json()["data"]

        # Create payment record
        payment = Payment(
            user_id=user_id,
            reference=data["reference"],
            amount=amount,
            status="pending",
        )
        session.add(payment)
        await session.commit()
        await session.refresh(payment)

        return PaystackInitializeResponse(**data)

    async def verify_transaction(self, session: AsyncSession, reference: str) -> PaystackVerifyResponse:
        url = f"{self.BASE_URL}/transaction/verify/{reference}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Paystack verification failed: {response.text}"
            )

        resp_json = response.json()
        data = resp_json["data"]
        paystack_status = data.get("status", "failed")  # success | failed | abandoned
        amount_naira = data.get("amount", 0) / 100  # convert kobo → Naira

        # Fetch local payment record
        statement = select(Payment).where(Payment.reference == reference)
        results = await session.exec(statement)
        payment = results.first()

        if payment:
            # Guard against amount tampering
            expected_amount_kobo = int(payment.amount * 100)
            if data.get("amount") != expected_amount_kobo:
                print(f"Warning: Payment amount mismatch. Expected: {expected_amount_kobo}, Got: {data.get('amount')}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "payment_status": "failed",
                        "is_paid": False,
                        "message": "Payment amount mismatch — possible fraud attempt",
                        "reference": reference,
                        "amount": amount_naira,
                    }
                )

            if paystack_status == "success" and payment.status != "success":
                payment.status = "success"
                payment.paid_at = (
                    datetime.fromisoformat(data["paid_at"].replace("Z", "+00:00"))
                    if data.get("paid_at") else None
                )
                payment.channel = data.get("channel")
                payment.updated_at = datetime.now(timezone.utc)
                session.add(payment)

                # Link to ConfessForm if metadata exists
                metadata = data.get("metadata")
                if metadata:
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except Exception:
                            metadata = {}

                    confess_form_id = metadata.get("confess_form_id")
                    if confess_form_id:
                        from app.models.confess_form import ConfessForm
                        confess_form = await session.get(ConfessForm, confess_form_id)
                        if confess_form:
                            confess_form.paid = True
                            session.add(confess_form)

                await session.commit()
                await session.refresh(payment)

        # ── Map Paystack status → HTTP response code ───────────────────────
        # success                        → 200 OK
        # pending | ongoing | processing | queued  → 202 Accepted
        # abandoned | failed | reversed  → 402 Payment Required
        PENDING_STATUSES = {"pending", "ongoing", "processing", "queued"}
        FAILED_STATUSES  = {"abandoned", "failed", "reversed"}

        STATUS_MESSAGES = {
            "success":    "Payment was successful",
            "abandoned":  "Payment was abandoned — user did not complete checkout",
            "failed":     "Payment failed — transaction was declined",
            "reversed":   "Payment was reversed (refunded or chargeback)",
            "pending":    "Payment is pending — transaction not yet completed",
            "ongoing":    "Payment is in progress — awaiting user action (e.g. OTP)",
            "processing": "Payment is processing — direct debit in progress",
            "queued":     "Payment is queued — scheduled for later processing",
        }

        message = STATUS_MESSAGES.get(paystack_status, f"Payment status: {paystack_status}")

        if paystack_status == "success":
            return PaystackVerifyResponse(
                payment_status=paystack_status,
                is_paid=True,
                message=message,
                reference=reference,
                amount=amount_naira,
            )

        if paystack_status in PENDING_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail={
                    "payment_status": paystack_status,
                    "is_paid": False,
                    "message": message,
                    "reference": reference,
                    "amount": amount_naira,
                }
            )

        # abandoned | failed | reversed
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "payment_status": paystack_status,
                "is_paid": False,
                "message": message,
                "reference": reference,
                "amount": amount_naira,
            }
        )

    async def list_transactions(self, session: AsyncSession, user_id: str):
        statement = select(Payment).where(Payment.user_id == user_id).order_by(Payment.created_at.desc())
        results = await session.exec(statement)
        return results.all()

    async def handle_webhook(self, session: AsyncSession, request_body: bytes, signature: str):
        # Verify signature
        hash = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
            request_body,
            hashlib.sha512
        ).hexdigest()

        if hash != signature:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signature"
            )

        event = json.loads(request_body)

        if event["event"] == "charge.success":
            data = event["data"]
            reference = data["reference"]

            statement = select(Payment).where(Payment.reference == reference)
            results = await session.exec(statement)
            payment = results.first()

            if payment and payment.status != "success":
                payment.status = "success"
                payment.paid_at = datetime.fromisoformat(data["paid_at"].replace("Z", "+00:00")) if data.get("paid_at") else None
                payment.channel = data.get("channel")
                payment.updated_at = datetime.now(timezone.utc)
                session.add(payment)

                # Link to ConfessForm if metadata exists
                metadata = data.get("metadata")
                if metadata:
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except:
                            metadata = {}

                    confess_form_id = metadata.get("confess_form_id")
                    if confess_form_id:
                        from app.models.confess_form import ConfessForm
                        confess_form = await session.get(ConfessForm, confess_form_id)
                        if confess_form:
                            confess_form.paid = True
                            session.add(confess_form)

                await session.commit()

        return {"status": "success"}

paystack_service = PaystackService()
