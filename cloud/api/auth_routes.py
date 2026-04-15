"""OAuth2 password flow + JWT (FastAPI-compatible token endpoint)."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .security import Token, UserOut, authenticate_user, create_access_token, require_user

router = APIRouter(prefix="/auth", tags=["auth"])


def get_db_session():
    from .main import telemetry

    session = telemetry.Session()
    try:
        yield session
    finally:
        session.close()


SessionDep = Annotated[Session, Depends(get_db_session)]


@router.post("/token", response_model=Token)
def login_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep,
):
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(sub=user.email, role=user.role)
    return Token(access_token=token)


class LoginJsonBody(BaseModel):
    email: str
    password: str


@router.post("/login", response_model=Token)
def login_json(body: LoginJsonBody, session: SessionDep):
    """Same as /auth/token but accepts JSON (convenient for SPA)."""
    user = authenticate_user(session, body.email, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token = create_access_token(sub=user.email, role=user.role)
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
def read_me(user: UserOut = Depends(require_user)):
    return user
