from pydantic import BaseModel


class GptRequest(BaseModel):
    text: str
    history: str | None = None