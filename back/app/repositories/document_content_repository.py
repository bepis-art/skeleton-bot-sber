from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.entities.base import DocumentContent


class DocumentContentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_document(self, document_id: UUID) -> DocumentContent | None:
        stmt = select(DocumentContent).where(DocumentContent.document_id == document_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add(self, content: DocumentContent) -> None:
        self.session.add(content)
        await self.session.commit()

    async def delete(self, content: DocumentContent) -> None:
        await self.session.delete(content)

class DocumentContentStreamRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def stream_all(self):
        async with self.session_factory() as session:
            stmt = select(DocumentContent.text)
            stream = await session.stream(stmt)

            async for row in stream:
                yield row.text
