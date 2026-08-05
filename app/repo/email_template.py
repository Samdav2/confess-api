from typing import Optional, List, Tuple
from uuid import UUID
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.email_template import AdminEmailTemplate


class EmailTemplateRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, template: AdminEmailTemplate) -> AdminEmailTemplate:
        self.session.add(template)
        await self.session.commit()
        await self.session.refresh(template)
        return template

    async def get_by_id(self, template_id: UUID) -> Optional[AdminEmailTemplate]:
        stmt = select(AdminEmailTemplate).where(AdminEmailTemplate.id == template_id)
        result = await self.session.exec(stmt)
        return result.first()

    async def get_all(
        self, skip: int = 0, limit: int = 50
    ) -> Tuple[List[AdminEmailTemplate], int]:
        total_stmt = select(func.count()).select_from(AdminEmailTemplate)
        total_res = await self.session.exec(total_stmt)
        total = total_res.one() or 0

        stmt = (
            select(AdminEmailTemplate)
            .order_by(AdminEmailTemplate.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.exec(stmt)
        return list(result.all()), total

    async def update(self, template: AdminEmailTemplate) -> AdminEmailTemplate:
        self.session.add(template)
        await self.session.commit()
        await self.session.refresh(template)
        return template

    async def delete(self, template_id: UUID) -> bool:
        template = await self.get_by_id(template_id)
        if not template:
            return False
        await self.session.delete(template)
        await self.session.commit()
        return True
