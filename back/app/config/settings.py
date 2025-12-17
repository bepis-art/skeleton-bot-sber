import os

from pydantic.v1 import BaseSettings


class Settings(BaseSettings):
    gigachat_credentials: str = os.getenv('GIGACHAT_CREDENTIALS')
    gigachat_scope: str = os.getenv('GIGACHAT_SCOPE')

    jwt_algorithm: str = 'HS256'
    jwt_secret: str = os.getenv('JWT_SECRET', 'secret')

    access_token_expire_minutes: int = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 30))
    refresh_token_expire_days: int = int(os.getenv('REFRESH_TOKEN_EXPIRE_DAYS', 30))

    client_url: str = os.getenv('CLIENT_URL', 'http://localhost:5173')

    database_url: str = os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@localhost:5432/helper')
    sync_database_url: str = database_url.replace('asyncpg', 'psycopg2')

settings = Settings()
