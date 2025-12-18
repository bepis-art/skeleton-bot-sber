from litestar import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.tokens import decode_token
from app.entities.base import User


class CurrentUser:
    def __init__(self, request: Request, session: AsyncSession):
        self.request = request
        self.session = session
        self.user = None
        self.checked = False

    async def get(self) -> User | None:
        if self.checked:
            return self.user

        user = await self.__get_current_user()

        self.user = user
        self.checked = True

        return user

    async def __get_current_user(self) -> User | None:
        auth = self.request.headers.get("authorization")
        if not auth or not auth.startswith("Bearer "):
            return None

        token = auth.split(" ")[1]

        try:
            payload = decode_token(token)
            user_id = payload["sub"]
        except Exception:
            return None

        return await self.session.get(User, user_id)

async def get_current_user(request: Request, session: AsyncSession) -> CurrentUser:
    return CurrentUser(request, session)
