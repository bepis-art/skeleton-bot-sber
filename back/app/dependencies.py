from litestar import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory
from app.repositories.document_content_repository import DocumentContentRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.document_service import DocumentService
from app.services.gpt_service import GptService
from app.services.rag_manager import RagManager


async def db_session():
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

async def provide_user_repository(session: AsyncSession) -> UserRepository:
    return UserRepository(session)

async def provide_refresh_token_repository(session: AsyncSession) -> RefreshTokenRepository:
    return RefreshTokenRepository(session)

async def provide_document_repository(session: AsyncSession) -> DocumentRepository:
    return DocumentRepository(session)

async def provide_document_content_repository(session: AsyncSession) -> DocumentContentRepository:
    return DocumentContentRepository(session)


async def provide_auth_service(user_repository: UserRepository, refresh_token_repository: RefreshTokenRepository) -> AuthService:
    return AuthService(user_repository, refresh_token_repository)


def provide_rag_manager(request: Request) -> RagManager:
    return request.app.state.rag_manager

async def provide_gpt_service(rag_manager: RagManager) -> GptService:
    return GptService(rag_manager)


async def provide_document_service(document_repository: DocumentRepository, document_content_repository: DocumentContentRepository, rag_manager: RagManager) -> DocumentService:
    return DocumentService(document_repository, document_content_repository, rag_manager)
