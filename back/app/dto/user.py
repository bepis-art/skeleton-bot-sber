from pydantic import BaseModel, UUID4

from app.entities.user import UserRole


class UserResponse(BaseModel):
    id: UUID4
    login: str
    password: str
    role: UserRole

    class Config:
        from_attributes = True
