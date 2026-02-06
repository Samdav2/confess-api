from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.confess_form import ConfessForm
from app.schemas.confess_form import ConfessFormCreate, ConfessFormUpdate, ConfessFormResponse, ConfessFormListResponse
from app.repo.confess_form import ConfessFormRepository
from app.service.groq_service import GroqService
from app.models.confess_form import ConfessForm, ConfessionAIMessage
from fastapi import HTTPException, status, BackgroundTasks
import os
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")


class ConfessFormService:
    def __init__(self, session: AsyncSession):
        self.repository = ConfessFormRepository(session)
        api_key = API_KEY
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Initializing ConfessFormService with API key starting with: {api_key[:5] if api_key else 'NONE'}")
        self.groq_service = GroqService(api_key)

    def _generate_unique_slug(self) -> str:
        """Generate a random 8-character slug"""
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(8))

    async def create_confess_form(
            self,
            user_id: UUID,
            confess_data: ConfessFormCreate
    ) -> ConfessFormResponse:
        """Create a new confess form"""
        # Validate delivery method requirements
        if confess_data.delivery == "email" and not confess_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required when delivery method is EMAIL"
            )

        if confess_data.delivery == "whatsapp" and not confess_data.phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number is required when delivery method is WHATSAPP"
            )

        # Generate unique slug
        slug = self._generate_unique_slug()
        while await self.repository.get_by_slug(slug):
            slug = self._generate_unique_slug()

        # Create confess form
        confess_form = ConfessForm(
            user_id=user_id,
            slug=slug,
            **confess_data.model_dump()
        )

        print("API_KEY#############: ", API_KEY)

        created_form = await self.repository.create(confess_form)

        # Generate and save AI message
        try:
            ai_message_text = await self.groq_service.generate_confession_message(
                tone=confess_data.tone,
                confess_type=confess_data.confess_type,
                recipient_name=confess_data.recipient_name
            )

            ai_message = ConfessionAIMessage(
                confess_form_id=created_form.id,
                message=ai_message_text
            )
            self.repository.session.add(ai_message)
            await self.repository.session.commit()

            # Refresh form to get the relationship
            await self.repository.session.refresh(created_form)

        except Exception as e:
            # Log error but don't fail the request
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to generate AI message: {e}", exc_info=True)

        # Try to use the direct generated text first for the response
        final_ai_message = ai_message_text if 'ai_message_text' in locals() else (created_form.ai_message.message if created_form.ai_message else None)

        return ConfessFormResponse(
            **created_form.model_dump(),
            ai_message=final_ai_message
        )

    async def get_confess_form(
            self,
            confess_id: UUID,
            user_id: Optional[UUID] = None
    ) -> ConfessFormResponse:
        """Get a confess form by ID"""
        confess_form = await self.repository.get_by_id(confess_id)

        if not confess_form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Confess form not found"
            )

        # If user_id is provided, verify ownership
        if user_id and confess_form.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this confess form"
            )

        return ConfessFormResponse(
            **confess_form.model_dump(),
            ai_message=confess_form.ai_message.message if confess_form.ai_message else None
        )

    async def get_confess_form_by_slug(
            self,
            slug: str
    ) -> ConfessFormResponse:
        """Get a confess form by slug"""
        confess_form = await self.repository.get_by_slug(slug)

        if not confess_form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Confess form not found"
            )

        return ConfessFormResponse(
            **confess_form.model_dump(),
            ai_message=confess_form.ai_message.message if confess_form.ai_message else None
        )

    async def get_user_confess_forms(
            self,
            user_id: UUID,
            page: int = 1,
            page_size: int = 10,
            confess_type: Optional[str] = None
    ) -> ConfessFormListResponse:
        """Get all confess forms for a user"""
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page must be greater than 0"
            )

        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page size must be between 1 and 100"
            )

        skip = (page - 1) * page_size
        confess_forms, total = await self.repository.get_by_user_id(
            user_id=user_id,
            skip=skip,
            limit=page_size,
            confess_type=confess_type
        )

        return ConfessFormListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[
                ConfessFormResponse(
                    **cf.model_dump(),
                    ai_message=cf.ai_message.message if cf.ai_message else None
                ) for cf in confess_forms
            ]
        )

    async def update_confess_form(
            self,
            confess_id: UUID,
            user_id: UUID,
            update_data: ConfessFormUpdate
    ) -> ConfessFormResponse:
        """Update a confess form"""
        # Check ownership
        confess_form = await self.repository.get_by_id(confess_id)
        if not confess_form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Confess form not found"
            )

        if confess_form.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this confess form"
            )

        # Filter out None values
        update_dict = update_data.model_dump(exclude_unset=True)

        # Validate delivery method if being updated
        if 'delivery' in update_dict:
            if update_dict['delivery'] == "email" and not (update_dict.get('email') or confess_form.email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email is required when delivery method is EMAIL"
                )
            if update_dict['delivery'] == "whatsapp" and not (update_dict.get('phone') or confess_form.phone):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Phone number is required when delivery method is WHATSAPP"
                )

        updated_form = await self.repository.update(confess_id, update_dict)
        return ConfessFormResponse(
            **updated_form.model_dump(),
            ai_message=updated_form.ai_message.message if updated_form.ai_message else None
        )

    async def delete_confess_form(
            self,
            confess_id: UUID,
            user_id: UUID
    ) -> None:
        """Delete a confess form"""
        # Check ownership
        confess_form = await self.repository.get_by_id(confess_id)
        if not confess_form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Confess form not found"
            )

        if confess_form.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this confess form"
            )

        await self.repository.delete(confess_id)

    async def submit_answer(
            self,
            slug: str,
            answer: bool,
            background_tasks: BackgroundTasks,
            date_proposal: Optional[datetime] = None
    ) -> dict:
        """Submit an answer to a confess form"""
        confess_form = await self.repository.get_by_slug(slug)
        if not confess_form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Confess form not found"
            )

        # Update database
        update_data = {"date_answer": answer}
        if date_proposal:
            update_data["recipient_date_proposal"] = date_proposal

        updated_form = await self.repository.update(confess_form.id, update_data)

        # Send Notification to the Sender (User)
        # Verify we have the user email
        sender_email = confess_form.user.email
        sender_name = confess_form.sender_name or "Anonymous" # Or user.username if appropriate

        from app.dependencies.email_service import email_service

        if sender_email:
             # If a new date is proposed, send a reschedule notification
             if date_proposal:
                 email_service.send_confess_reschedule_notification(
                    background_tasks=background_tasks,
                    email_to=sender_email,
                    sender_name=sender_name,
                    recipient_name=confess_form.recipient_name or "The Recipient",
                    new_date=date_proposal,
                    confess_type=confess_form.confess_type,
                    slug=slug
                )
             else:
                 email_service.send_confess_response_notification(
                    background_tasks=background_tasks,
                    email_to=sender_email,
                    sender_name=sender_name,
                    recipient_name=confess_form.recipient_name or "The Recipient",
                    response=answer,
                    confess_type=confess_form.confess_type,
                    slug=slug
                )

        return {"message": "Answer submitted successfully", "answer": answer, "date_proposal": date_proposal}

    async def send_confess_form(
            self,
            slug: str,
            background_tasks: BackgroundTasks
    ) -> dict:
        """
        Send confess form via Email or WhatsApp based on available contact info.
        """
        confess_form = await self.repository.get_by_slug(slug)
        if not confess_form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Confess form not found"
            )

        from app.dependencies.email_service import email_service

        # Logic:
        # 1. If phone is null -> Send Email
        # 2. If email is null and phone is not null -> Send WhatsApp
        # 3. Default fallback (if both exist, priority to Email as per "phone is null" check) -> Email

        if not confess_form.phone:
            # Send Email
            if not confess_form.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No email address available for this form"
                )

            email_service.send_confess_notification(
                background_tasks=background_tasks,
                email_to=confess_form.email,
                name=confess_form.recipient_name or "Friend",
                sender_name=confess_form.sender_name or "Someone", # You might want to get this from user_id if not anonymous
                message=confess_form.message,
                confess_type=confess_form.confess_type,
                slug=slug
            )
            return {"message": "Notification sent via Email"}

        elif not confess_form.email and confess_form.phone:
            # Send WhatsApp
            # TODO: Implement actual WhatsApp integration
            # For now, we log it as a placeholder
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Mocking WhatsApp send to {confess_form.phone}: {confess_form.message}")

            return {"message": "Notification sent via WhatsApp (Mock)"}

        else:
            # Both exist, default to Email (or whatever priority logic implies)
             email_service.send_confess_notification(
                background_tasks=background_tasks,
                email_to=confess_form.email,
                name=confess_form.recipient_name or "Friend",
                sender_name=confess_form.sender_name or "Someone",
                message=confess_form.message,
                confess_type=confess_form.confess_type,
                slug=slug
            )
             return {"message": "Notification sent via Email"}
