from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.base import RefreshToken


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, token: str) -> RefreshToken | None:
        return await self.session.scalar(
            select(RefreshToken).where(RefreshToken.token == token)
        )

    async def add(self, refresh_token: RefreshToken):
        self.session.add(refresh_token)
        await self.session.flush()

    async def revoke(self, token: str):
        token_obj = await self.get(token)
        if token_obj:
            token_obj.revoked = True
