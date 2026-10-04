import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.api.v1 import admin, auth, documents, family, files, me, notifications, policies, support
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
    for module in (auth, me, family, documents, policies, notifications, support, files, admin):
        app.include_router(module.router, prefix=s.api_prefix)

    admin_page = Path(__file__).parent / "static" / "admin.html"

    @app.get("/admin", include_in_schema=False)
    def admin_ui() -> FileResponse:
        return FileResponse(admin_page, headers={"Cache-Control": "no-store", "X-Frame-Options": "DENY"})

    @app.get("/health", tags=["ops"])
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
