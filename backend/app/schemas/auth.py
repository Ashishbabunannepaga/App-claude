from pydantic import BaseModel, Field

from app.schemas.user import UserOut


class OtpRequest(BaseModel):
    identifier: str = Field(min_length=5, max_length=320, description="Mobile number or email")


class OtpRequestOut(BaseModel):
    identifier: str
    expires_in: int
    resend_after: int


class OtpVerify(BaseModel):
    identifier: str = Field(min_length=5, max_length=320)
    code: str = Field(pattern=r"^\d{6}$")
    consent: bool = Field(False, description="User accepted privacy notice & terms (required for new users)")


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20, max_length=200)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthOut(TokenPair):
    user: UserOut
    is_new_user: bool
