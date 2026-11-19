from fastapi import APIRouter

from app.api.deps import DB, CurrentUser
from app.core.errors import AppError
from app.core.rate_limit import limiter
from app.models import SupportRequest
from app.schemas.account import SupportIn

router = APIRouter(tags=["support"])


@router.post("/support", status_code=201)
def create_request(body: SupportIn, user: CurrentUser, db: DB) -> dict:
    limiter.hit(f"support:{user.id}", limit=10, window_seconds=3600)
    if body.category == "expert_review" and not user.contact_consent:
        # An expert call is CapitUp's team contacting the client: it needs the "CapitUp may contact me" consent,
        # which the app asks for in the same dialog. It also puts the request in the LMS leads feed.
        raise AppError("contact_consent_required", "Allow CapitUp to contact you so an expert can call you.", 400)
    req = SupportRequest(user_id=user.id, category=body.category, message=body.message)
    db.add(req)
    db.commit()
    return {"id": str(req.id), "status": req.status}
