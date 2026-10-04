import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, documents, files, me, policies
from app.core.config import get_settings
from app.core.errors import install_error_handlers


def create_app() -> FastAPI:
    s = get_settings()
    logging.basicConfig(level=logging.INFO)
    is_prod = s.env == "production"
    app = FastAPI(
        title=s.app_name,
        version="0.1.0",
        docs_url=None if is_prod else "/docs",
        redoc_url=None,
        openapi_url=None if is_prod else "/openapi.json",
    )
    if s.cors_origins:
        app.add_middleware(CORSMiddleware, allow_origins=s.cors_origins, allow_methods=["*"], allow_headers=["*"])
    install_error_handlers(app)
    for module in (auth, me, documents, policies, files):
        app.include_router(module.router, prefix=s.api_prefix)

    @app.get("/health", tags=["ops"])
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
