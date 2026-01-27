from typing import Optional, List
from uuid import UUID
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from app.models.confess_form import ConfessForm, ConfessType, DeliveryMethod


class ConfessFormRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, confess_form: ConfessForm) -> ConfessForm:
        """Create a new confess form"""
        self.session.add(confess_form)
        await self.session.commit()
        await self.session.refresh(confess_form)
        return confess_form

    async def get_by_id(self, confess_id: UUID) -> Optional[ConfessForm]:
        """Get confess form by ID"""
        statement = select(ConfessForm).where(ConfessForm.id == confess_id)
        result = await self.session.exec(statement)
        return result.first()

    async def get_by_slug(self, slug: str) -> Optional[ConfessForm]:
        """Get confess form by slug"""
        statement = select(ConfessForm).where(ConfessForm.slug == slug)
        result = await self.session.exec(statement)
        return result.first()

    async def get_by_user_id(
            self,
            user_id: UUID,
            skip: int = 0,
            limit: int = 10,
            confess_type: Optional[ConfessType] = None
    ) -> tuple[List[ConfessForm], int]:
        """Get all confess forms for a user with pagination"""
        statement = select(ConfessForm).where(ConfessForm.user_id == user_id)

        if confess_type:
            statement = statement.where(ConfessForm.confess_type == confess_type)

        # Get total count
        count_statement = select(ConfessForm).where(ConfessForm.user_id == user_id)
        if confess_type:
            count_statement = count_statement.where(ConfessForm.confess_type == confess_type)
        count_result = await self.session.exec(count_statement)
        total = len(count_result.all())

        # Get paginated results
        statement = statement.order_by(ConfessForm.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.exec(statement)
        results = result.all()

        return results, total

    async def get_all(
            self,
            skip: int = 0,
            limit: int = 10,
            confess_type: Optional[ConfessType] = None,
            delivery: Optional[DeliveryMethod] = None
    ) -> tuple[List[ConfessForm], int]:
        """Get all confess forms with optional filters and pagination"""
        statement = select(ConfessForm)

        if confess_type:
            statement = statement.where(ConfessForm.confess_type == confess_type)
        if delivery:
            statement = statement.where(ConfessForm.delivery == delivery)

        # Get total count
        count_statement = select(ConfessForm)
        if confess_type:
            count_statement = count_statement.where(ConfessForm.confess_type == confess_type)
        if delivery:
            count_statement = count_statement.where(ConfessForm.delivery == delivery)
        count_result = await self.session.exec(count_statement)
        total = len(count_result.all())

        # Get paginated results
        statement = statement.order_by(ConfessForm.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.exec(statement)
        results = result.all()

        return results, total

    async def update(self, confess_id: UUID, update_data: dict) -> Optional[ConfessForm]:
        """Update a confess form"""
        confess_form = await self.get_by_id(confess_id)
        if not confess_form:
            return None

        for key, value in update_data.items():
            if value is not None:
                setattr(confess_form, key, value)

        confess_form.updated_at = datetime.now(timezone.utc)
        self.session.add(confess_form)
        await self.session.commit()
        await self.session.refresh(confess_form)
        return confess_form

    async def delete(self, confess_id: UUID) -> bool:
        """Delete a confess form"""
        confess_form = await self.get_by_id(confess_id)
        if not confess_form:
            return False

        await self.session.delete(confess_form)
        await self.session.commit()
        return True

    async def exists(self, confess_id: UUID) -> bool:
        """Check if confess form exists"""
        result = await self.get_by_id(confess_id)
        return result is not None
