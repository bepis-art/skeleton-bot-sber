from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.gpt_service import GptService
from app.services.rag_service import RagService


async def db_session():
    async with async_session_factory() as session:
        yield session


async def provide_user_repository(session: AsyncSession) -> UserRepository:
    return UserRepository(session)

async def provide_refresh_token_repository(session: AsyncSession) -> RefreshTokenRepository:
    return RefreshTokenRepository(session)


async def provide_auth_service(user_repository: UserRepository, refresh_token_repository: RefreshTokenRepository) -> AuthService:
    return AuthService(user_repository, refresh_token_repository)


async def provide_rag_service() -> RagService:
    return RagService()

async def provide_gpt_service(rag_service: RagService) -> GptService:
    return GptService(rag_service)