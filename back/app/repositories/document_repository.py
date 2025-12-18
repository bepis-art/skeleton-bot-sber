from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.base import Document


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, document_id: UUID) -> Document | None:
        return await self.session.get(Document, document_id)

    async def get_all(self) -> list[Document]:
        documents = await self.session.execute(select(Document))
        return list(documents.scalars().all())

    async def add(self, document: Document) -> None:
        self.session.add(document)
        await self.session.flush()
