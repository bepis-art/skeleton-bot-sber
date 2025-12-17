from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, token: str) -> RefreshToken | None:
        return await self.session.scalar(
            select(RefreshToken).where(RefreshToken.token == token)
        )

    async def add(self, refresh_token: RefreshToken):
        self.session.add(refresh_token)
        await self.session.commit()
        await self.session.refresh(refresh_token)

    async def revoke(self, refresh_token: RefreshToken):
        refresh_token.revoked = True
        await self.session.commit()
        await self.session.refresh(refresh_token)