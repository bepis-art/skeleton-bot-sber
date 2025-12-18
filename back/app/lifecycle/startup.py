from pathlib import Path

from alembic import command
from alembic.config import Config
from litestar import Litestar

from app.db.session import async_session_factory
from app.repositories.document_content_repository import DocumentContentStreamRepository
from app.services.rag_manager import RagManager
from app.services.rag_service import RagService


def run_migrations():
    alembic_cfg = Config(
        str(Path(__file__).parents[2] / "alembic.ini"),
    )
    command.upgrade(alembic_cfg, "head")

def init_rag(app: Litestar) -> None:
    document_content_repository = DocumentContentStreamRepository(async_session_factory)
    default_rag = RagService(document_content_repository)
    app.state.rag_manager = RagManager(default_rag, document_content_repository)
