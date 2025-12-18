from pydantic import BaseModel, UUID4


class DocumentDownload(BaseModel):
    filename: str
    mime_type: str
    content: bytes

class DocumentResponse(BaseModel):
    id: UUID4
    filename: str
    mime_type: str
    size: int

    class Config:
        from_attributes = True
