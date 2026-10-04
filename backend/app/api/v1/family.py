import uuid

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import DB, CurrentUser
from app.core.errors import NotFound
from app.models import FamilyMember
from app.schemas.account import MemberIn, MemberUpdate
from app.schemas.policy import MemberOut

router = APIRouter(prefix="/me/family", tags=["family"])


def _owned(db, user_id: uuid.UUID, member_id: uuid.UUID) -> FamilyMember:
    member = db.scalar(select(FamilyMember).where(FamilyMember.id == member_id, FamilyMember.user_id == user_id))
    if member is None:
        raise NotFound("Family member")
    return member


@router.get("", response_model=list[MemberOut])
def list_members(user: CurrentUser, db: DB) -> list[FamilyMember]:
    return list(
        db.scalars(select(FamilyMember).where(FamilyMember.user_id == user.id).order_by(FamilyMember.created_at))
    )


@router.post("", response_model=MemberOut, status_code=201)
def add_member(body: MemberIn, user: CurrentUser, db: DB) -> FamilyMember:
    member = FamilyMember(user_id=user.id, **body.model_dump())
    db.add(member)
    db.commit()
    return member


@router.patch("/{member_id}", response_model=MemberOut)
def update_member(member_id: uuid.UUID, body: MemberUpdate, user: CurrentUser, db: DB) -> FamilyMember:
    member = _owned(db, user.id, member_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(member, field, value)
    db.commit()
    return member


@router.delete("/{member_id}", status_code=204)
def delete_member(member_id: uuid.UUID, user: CurrentUser, db: DB) -> None:
    db.delete(_owned(db, user.id, member_id))
    db.commit()
