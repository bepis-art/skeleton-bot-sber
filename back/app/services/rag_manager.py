import asyncio
from typing import Optional

from app.repositories.document_content_repository import DocumentContentStreamRepository
from app.services.rag_service import RagService


class RagManager:
    def __init__(self, initial: RagService, document_content_repository: DocumentContentStreamRepository):
        self.__rag = initial
        self.__lock = asyncio.Lock()
        self.__task: Optional[asyncio.Task] = None
        self.__document_content_repository = document_content_repository

        self.start_rebuild()

    def get(self) -> RagService:
        return self.__rag

    def start_rebuild(self) -> None:
        if self.__task and not self.__task.done():
            self.__task.cancel()

        self.__task = asyncio.create_task(self.__rebuild())

    async def __rebuild(self) -> None:
        try:
            new_rag = await self.__build()
            if new_rag is None:
                return

        except asyncio.CancelledError:
            return

        except Exception as e:
            print(e)
            return

        async with self.__lock:
            self.__rag = new_rag

    async def __build(self) -> RagService | None:
        try:
            rag = RagService(self.__document_content_repository)

            await asyncio.sleep(0)

            result = await rag.load_all_documents()

            return rag if result else None

        except asyncio.CancelledError:
            return None
