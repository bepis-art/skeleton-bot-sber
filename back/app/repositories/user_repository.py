from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.user import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_login(self, login: str) -> User | None:
        return await self.session.scalar(
            select(User).where(User.login == login)
        )

    async def add(self, user: User):
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
