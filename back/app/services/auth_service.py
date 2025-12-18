from datetime import datetime, timezone

from app.auth.security import get_password_hash, verify_password
from app.auth.tokens import create_access_token, create_refresh_token
from app.entities.base import RefreshToken, User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, user_repository: UserRepository, refresh_token_repository: RefreshTokenRepository):
        self.user_repository = user_repository
        self.refresh_token_repository = refresh_token_repository

    async def register(self, login: str, password: str) -> User:
        existing = await self.user_repository.get_by_login(login)
        if existing:
            raise ValueError("User with login '{}' already exists".format(login))

        hashed_pwd = get_password_hash(password)
        user = User(
            login=login,
            password=hashed_pwd
        )

        await self.user_repository.add(user)

        return user

    async def login(self, login: str, password: str) -> dict:
        user = await self.user_repository.get_by_login(login)
        if not user or not verify_password(password, str(user.password)):
            raise ValueError("Invalid credentials")

        access_token = create_access_token(str(user.id), str(user.role))
        refresh_token, expires_at = create_refresh_token()

        await self.refresh_token_repository.add(RefreshToken(
            token=refresh_token,
            user_id=user.id,
            expires_at=expires_at
        ))

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    async def refresh(self, refresh_token: str) -> dict:
        token_obj = await self.refresh_token_repository.get(refresh_token)

        if not token_obj or token_obj.revoked or token_obj.expires_at < datetime.now(timezone.utc):
            raise ValueError("Invalid refresh token")

        user = await self.user_repository.get_by_id(token_obj.user_id)
        new_access_token = create_access_token(str(user.id), str(user.role))

        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }

    async def logout(self, refresh_token: str) -> None:
        await self.refresh_token_repository.revoke(refresh_token)