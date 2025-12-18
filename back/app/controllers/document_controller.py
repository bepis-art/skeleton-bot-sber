from typing import Annotated, List
from uuid import UUID

from litestar import Controller, get, Response, post, MediaType
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body

from app.dto.document import DocumentResponse
from app.dto.multipart import MultipartData
from app.services.document_service import DocumentService


class DocumentController(Controller):
    path = "/document"

    @get()
    async def get_meta(self, document_service: DocumentService) -> List[DocumentResponse]:
        documents = await document_service.get_documents_meta()
        return list([DocumentResponse.model_validate(document) for document in documents])

    @post("/upload")
    async def upload(self, data: Annotated[MultipartData, Body(media_type=RequestEncodingType.MULTI_PART)], document_service: DocumentService) -> DocumentResponse:
        file = data.file
        content: bytes = await file.read()
        filename = file.filename
        mime_type = file.content_type

        document = await document_service.upload(filename, mime_type, content)

        return DocumentResponse.model_validate(document)

    @get("/{document_id:uuid}")
    async def download(self, document_id: UUID, document_service: DocumentService) -> Response[bytes]:
        result = await document_service.download(document_id)

        return Response(
            content=result.content,
            media_type=result.mime_type,
            headers={
                "Content-Disposition": f"attachment; filename={result.filename}"
            }
        )