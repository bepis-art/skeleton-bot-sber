from fastapi import FastAPI
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware

from gpt_module import GPTModule

class TextInput(BaseModel):
    text: str
    history: str | None = None

app = FastAPI()
gpt = GPTModule()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/ask")
async def ask(data: TextInput):
    response = await gpt.process(data.text, data.history)
    return {"text": response}