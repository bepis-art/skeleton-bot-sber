from litestar import Controller, post

from app.dto.gpt import GptRequest
from app.services.gpt_service import GptService


class GptController(Controller):
    path = "/gpt"

    @post("/ask")
    async def ask(self, data: GptRequest, gpt_service: GptService) -> dict:
        response = await gpt_service.process(data.text, data.history)
        return {"text": response}
