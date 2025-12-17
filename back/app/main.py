from litestar import Litestar
from litestar.config.cors import CORSConfig
from litestar.di import Provide

from app.config.settings import settings
from app.controllers.auth_controller import AuthController
from app.controllers.gpt_controller import GptController
from app.dependencies import db_session, provide_user_repository, provide_auth_service, \
    provide_refresh_token_repository, provide_gpt_service, provide_rag_service
from app.lifecycle.startup import run_migrations

app = Litestar(
    route_handlers=[AuthController, GptController],
    cors_config=CORSConfig(
            allow_origins=[
                settings.client_url,
            ],
            allow_methods=['*'],
            allow_headers=['*'],
            allow_credentials=True,
    ),
    on_startup=[run_migrations],
    dependencies={
        "session": Provide(db_session),
        "user_repository": Provide(provide_user_repository),
        "refresh_token_repository": Provide(provide_refresh_token_repository),
        "auth_service": Provide(provide_auth_service),
        "rag_service": Provide(provide_rag_service),
        "gpt_service": Provide(provide_gpt_service)
    },
    debug=True
)
