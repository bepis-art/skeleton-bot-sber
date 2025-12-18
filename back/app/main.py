from litestar import Litestar
from litestar.config.cors import CORSConfig
from litestar.di import Provide

from app.config.settings import settings
from app.controllers.auth_controller import AuthController
from app.controllers.document_controller import DocumentController
from app.controllers.gpt_controller import GptController
from app.dependencies import db_session, provide_user_repository, provide_auth_service, \
    provide_refresh_token_repository, provide_gpt_service, provide_rag_manager, provide_document_repository, \
    provide_document_service, provide_document_content_repository
from app.lifecycle.startup import run_migrations, init_rag


app = Litestar(
    route_handlers=[AuthController, GptController, DocumentController],
    cors_config=CORSConfig(
            allow_origins=[
                settings.client_url,
            ],
            allow_methods=['*'],
            allow_headers=['*'],
            allow_credentials=True,
    ),
    on_startup=[run_migrations, init_rag],
    dependencies={
        "session": Provide(db_session),
        "user_repository": Provide(provide_user_repository),
        "refresh_token_repository": Provide(provide_refresh_token_repository),
        "document_repository": Provide(provide_document_repository),
        "document_content_repository": Provide(provide_document_content_repository),
        "auth_service": Provide(provide_auth_service),
        "rag_manager": Provide(provide_rag_manager, sync_to_thread=True),
        "gpt_service": Provide(provide_gpt_service),
        "document_service": Provide(provide_document_service)
    },
    debug=True
)
