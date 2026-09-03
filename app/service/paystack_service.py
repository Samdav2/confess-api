import hmac
import hashlib
import json
import httpx
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import HTTPException, status, BackgroundTasks
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config.settings import settings
from app.models.payment import Payment
from app.schemas.paystack import PaystackInitializeResponse, PaystackVerifyResponse


class PaystackService:
    BASE_URL = "https://api.paystack.co"

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }

    async def initialize_transaction(
        self,
        session: AsyncSession,
        user_id: str,
        email: str,
        amount: float,
        callback_url: str = None,
        confess_form_id: str = None,
        celebration_id: str = None,
        additional_metadata: dict = None
    ) -> PaystackInitializeResponse:
        url = f"{self.BASE_URL}/transaction/initialize"
        amount_kobo = int(amount * 100)

        metadata = {"user_id": str(user_id)}
        if confess_form_id:
            metadata["confess_form_id"] = str(confess_form_id)
        if celebration_id:
            metadata["celebration_id"] = str(celebration_id)

        if additional_metadata:
            metadata.update(additional_metadata)

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

    async def verify_transaction(
        self,
        session: AsyncSession,
        reference: str,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> PaystackVerifyResponse:
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
        amount_naira = data.get("amount", 0) / 100

        statement = select(Payment).where(Payment.reference == reference)
        results = await session.exec(statement)
        payment = results.first()

        if payment:
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
                    datetime.fromisoformat(data["paid_at"].replace("Z", "+00:00")).replace(tzinfo=None)
                    if data.get("paid_at") else None
                )
                payment.channel = data.get("channel")
                payment.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
                session.add(payment)

                metadata = data.get("metadata")
                confess_form_to_notify = None
                celebration_to_notify = None

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
                            if not confess_form.paid:
                                confess_form_to_notify = confess_form
                            confess_form.paid = True
                            session.add(confess_form)

                    celebration_id = metadata.get("celebration_id")
                    if celebration_id:
                        from app.models.celebration import CelebrationPage, PaymentStatus
                        celebration = await session.get(CelebrationPage, celebration_id)
                        if celebration:
                            if celebration.payment_status != PaymentStatus.PAID:
                                celebration_to_notify = celebration
                            celebration.payment_status = PaymentStatus.PAID
                            session.add(celebration)

                await session.commit()
                await session.refresh(payment)

                if background_tasks:
                    if confess_form_to_notify:
                        from app.service.confess_form import ConfessFormService
                        cf_service = ConfessFormService(session)
                        background_tasks.add_task(cf_service.send_confess_form, confess_form_to_notify.slug, background_tasks)

                    if celebration_to_notify:
                        from app.service.celebration_service import CelebrationService
                        cel_service = CelebrationService(session)
                        background_tasks.add_task(cel_service.send_celebration_notification, celebration_to_notify, background_tasks)

        PENDING_STATUSES = {"pending", "ongoing", "processing", "queued"}

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

    async def handle_webhook(
        self,
        session: AsyncSession,
        request_body: bytes,
        signature: str,
        background_tasks: Optional[BackgroundTasks] = None
    ):
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
                payment.paid_at = datetime.fromisoformat(data["paid_at"].replace("Z", "+00:00")).replace(tzinfo=None) if data.get("paid_at") else None
                payment.channel = data.get("channel")
                payment.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
                session.add(payment)

                metadata = data.get("metadata")
                confess_form_to_notify = None
                celebration_to_notify = None

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
                            if not confess_form.paid:
                                confess_form_to_notify = confess_form
                            confess_form.paid = True
                            session.add(confess_form)

                    celebration_id = metadata.get("celebration_id")
                    if celebration_id:
                        from app.models.celebration import CelebrationPage, PaymentStatus
                        celebration = await session.get(CelebrationPage, celebration_id)
                        if celebration:
                            if celebration.payment_status != PaymentStatus.PAID:
                                celebration_to_notify = celebration
                            celebration.payment_status = PaymentStatus.PAID
                            session.add(celebration)

                await session.commit()

                if background_tasks:
                    if confess_form_to_notify:
                        from app.service.confess_form import ConfessFormService
                        cf_service = ConfessFormService(session)
                        background_tasks.add_task(cf_service.send_confess_form, confess_form_to_notify.slug, background_tasks)

                    if celebration_to_notify:
                        from app.service.celebration_service import CelebrationService
                        cel_service = CelebrationService(session)
                        background_tasks.add_task(cel_service.send_celebration_notification, celebration_to_notify, background_tasks)

        return {"status": "success"}


paystack_service = PaystackService()
