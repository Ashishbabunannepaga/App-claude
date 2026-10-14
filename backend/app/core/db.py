from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


_url = get_settings().database_url
# Fail in seconds, not minutes, when Postgres is down (e.g. Docker not started): without a connect timeout a
# request can hang past the app's 60 s limit and the user only sees "the connection timed out".
engine = create_engine(
    _url,
    pool_pre_ping=True,
    pool_timeout=10,
    connect_args={"connect_timeout": 5} if _url.startswith("postgresql") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
