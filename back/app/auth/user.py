from litestar import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.tokens import decode_token
from app.entities.base import User


async def get_current_user(
        request: Request,
        session: AsyncSession,
) -> User | None:
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        return None

    token = auth.split(" ")[1]

    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
    except Exception:
        return None

    return await session.get(User, user_id)
