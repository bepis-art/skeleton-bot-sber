from litestar import post, Controller
from litestar.exceptions import HTTPException

from app.dto.auth import RegisterDTO, LoginDTO, RefreshDTO, LogoutDTO
from app.dto.user import UserResponse
from app.services.auth_service import AuthService


class AuthController(Controller):
    path = "/auth"

    @post("/register")
    async def register(self, data: RegisterDTO, auth_service: AuthService) -> UserResponse:
        try:
            user = await auth_service.register(data.login, data.password)
            return UserResponse.model_validate(user)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @post("/login")
    async def login(self, data: LoginDTO, auth_service: AuthService) -> dict:
        try:
            return await auth_service.login(data.login, data.password)
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e))

    @post("/refresh")
    async def refresh(self, data: RefreshDTO, auth_service: AuthService) -> dict:
        try:
            return await auth_service.refresh(data.refresh_token)
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e))

    @post("/logout")
    async def logout(self, data: LogoutDTO, auth_service: AuthService) -> None:
        return await auth_service.logout(data.refresh_token)
