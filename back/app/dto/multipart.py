from dataclasses import dataclass

from litestar.datastructures import UploadFile


@dataclass
class MultipartData:
    file: UploadFile