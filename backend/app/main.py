import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import text

from app.api.v1 import (
    admin,
    auth,
    client_errors,
    coverage,
    documents,
    family,
    files,
    intelligence,
    me,
    notifications,
    policies,
    support,
)
from app.core.config import get_settings
from app.core.db import engine
from app.core.errors import install_error_handlers
from app.core.observability import init_error_tracking


def create_app() -> FastAPI:
    s = get_settings()
    logging.basicConfig(level=logging.INFO)
    init_error_tracking("api")
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
    # intelligence before policies: its static paths (/policies/compare) must win over /policies/{id}.
    for module in (
        auth,
        client_errors,
        me,
        family,
        documents,
        intelligence,
        coverage,
        policies,
        notifications,
        support,
        files,
        admin,
    ):
        app.include_router(module.router, prefix=s.api_prefix)

    admin_page = Path(__file__).parent / "static" / "admin.html"

    @app.get("/admin", include_in_schema=False)
    def admin_ui() -> FileResponse:
        return FileResponse(admin_page, headers={"Cache-Control": "no-store", "X-Frame-Options": "DENY"})

    static = Path(__file__).parent / "static"
    page_headers = {"Cache-Control": "public, max-age=3600", "X-Frame-Options": "DENY"}

    # Public legal pages linked from the app and the store listings (Play requires a privacy policy URL).
    @app.get("/privacy", include_in_schema=False)
    def privacy() -> FileResponse:
        return FileResponse(static / "privacy.html", headers=page_headers)

    @app.get("/terms", include_in_schema=False)
    def terms() -> FileResponse:
        return FileResponse(static / "terms.html", headers=page_headers)

    @app.get("/legal.css", include_in_schema=False)
    def legal_css() -> FileResponse:
        return FileResponse(static / "legal.css", media_type="text/css", headers=page_headers)

    @app.get("/health", tags=["ops"])
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/health/ready", tags=["ops"])
    def ready() -> JSONResponse:
        """Liveness plus dependencies: what an uptime check or a confused developer should look at."""
        checks = {"database": "ok"}
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as exc:  # report, never crash the health check
            checks["database"] = f"unreachable ({type(exc).__name__})"
        ok = all(v == "ok" for v in checks.values())
        return JSONResponse({"status": "ok" if ok else "degraded", **checks}, status_code=200 if ok else 503)

    return app


app = create_app()
