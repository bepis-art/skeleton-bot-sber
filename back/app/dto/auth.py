from pydantic import BaseModel


class RegisterDTO(BaseModel):
    login: str
    password: str

class LoginDTO(BaseModel):
    login: str
    password: str

class RefreshDTO(BaseModel):
    refresh_token: str

class LogoutDTO(BaseModel):
    refresh_token: str
