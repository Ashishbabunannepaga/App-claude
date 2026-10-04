from fastapi import APIRouter

from app.api.deps import DB, CurrentUser
from app.core.rate_limit import limiter
from app.models import SupportRequest
from app.schemas.account import SupportIn

router = APIRouter(tags=["support"])


@router.post("/support", status_code=201)
def create_request(body: SupportIn, user: CurrentUser, db: DB) -> dict:
    limiter.hit(f"support:{user.id}", limit=10, window_seconds=3600)
    req = SupportRequest(user_id=user.id, category=body.category, message=body.message)
    db.add(req)
    db.commit()
    return {"id": str(req.id), "status": req.status}
