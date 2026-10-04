from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import Unauthorized
from app.core.security import decode_access_token
from app.models import User

_bearer = HTTPBearer(auto_error=False)

DB = Annotated[Session, Depends(get_db)]


def get_current_user(db: DB, creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]) -> User:
    if creds is None:
        raise Unauthorized()
    user = db.get(User, decode_access_token(creds.credentials))
    if user is None or user.deletion_requested_at is not None:
        raise Unauthorized()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def client_ip(request: Request) -> str | None:
    # TODO(deploy): trust X-Forwarded-For only from the load balancer (uvicorn --proxy-headers).
    return request.client.host if request.client else None
