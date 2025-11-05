from fastapi import FastAPI
from pydantic import BaseModel

from GPTModule import GPTModule

class TextInput(BaseModel):
    text: str
    history: str | None = None

app = FastAPI()
gpt = GPTModule()

@app.post("/ask")
async def ask(data: TextInput):
    response = await gpt.process(data.text, data.history)
    return {"text": response}