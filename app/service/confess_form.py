from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.confess_form import ConfessForm
from app.schemas.confess_form import ConfessFormCreate, ConfessFormUpdate, ConfessFormResponse, ConfessFormListResponse
from app.repo.confess_form import ConfessFormRepository
from fastapi import HTTPException, status, BackgroundTasks


class ConfessFormService:
    def __init__(self, session: AsyncSession):
        self.repository = ConfessFormRepository(session)

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

        created_form = await self.repository.create(confess_form)
        return ConfessFormResponse.model_validate(created_form)

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

        return ConfessFormResponse.model_validate(confess_form)

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
            items=[ConfessFormResponse.model_validate(cf) for cf in confess_forms]
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
        return ConfessFormResponse.model_validate(updated_form)

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
                name=confess_form.name or "Friend",
                sender_name="Someone", # You might want to get this from user_id if not anonymous
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
                name=confess_form.name or "Friend",
                sender_name="Someone",
                message=confess_form.message,
                confess_type=confess_form.confess_type,
                slug=slug
            )
             return {"message": "Notification sent via Email"}
