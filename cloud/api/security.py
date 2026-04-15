"""JWT auth, password hashing, and role checks (operator vs admin)."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from .telemetry import APIUser

# pbkdf2_sha256 avoids native bcrypt / passlib version skew in some CI and dev images.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("PARKSIGHT_JWT_EXPIRE_MINUTES", "480"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


def _require_auth_enabled() -> bool:
    return os.getenv("PARKSIGHT_REQUIRE_AUTH", "").lower() in ("1", "true", "yes")


def _jwt_secret() -> str:
    secret = os.getenv("PARKSIGHT_JWT_SECRET", "")
    if _require_auth_enabled() and not secret:
        raise RuntimeError("PARKSIGHT_JWT_SECRET is required when PARKSIGHT_REQUIRE_AUTH=1")
    return secret or "dev-only-insecure-secret-change-with-parksight-jwt-secret"


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    role: str


class AuthError(Exception):
    pass


def parse_authorization_header(authorization: Optional[str]) -> UserOut:
    """Validate Bearer token (JWT or PARKSIGHT_SERVICE_BEARER). Raises AuthError."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthError("Missing or invalid Authorization header")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise AuthError("Empty bearer token")
    service = os.getenv("PARKSIGHT_SERVICE_BEARER", "").strip()
    if service and token == service:
        return UserOut(id=0, email="service@edge", role="operator")
    try:
        payload = decode_token(token)
        email = str(payload.get("sub") or "")
        role = str(payload.get("role") or "operator")
        if not email:
            raise AuthError("Invalid token")
        return UserOut(id=0, email=email, role=role)
    except JWTError as e:
        raise AuthError("Invalid or expired token") from e


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(*, sub: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {"sub": sub, "role": role, "exp": expire}
    return jwt.encode(payload, _jwt_secret(), algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, _jwt_secret(), algorithms=[ALGORITHM])


def get_user_by_email(session: Session, email: str) -> Optional[APIUser]:
    return session.scalars(select(APIUser).where(APIUser.email == email)).first()


def authenticate_user(session: Session, email: str, password: str) -> Optional[APIUser]:
    user = get_user_by_email(session, email)
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def bootstrap_users(engine: Engine) -> None:
    """Seed admin/operator from env when table is empty."""
    from sqlalchemy.orm import sessionmaker

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        n = session.scalars(select(APIUser.id).limit(1)).first()
        if n is not None:
            return
        admin_email = os.getenv("PARKSIGHT_ADMIN_EMAIL", "admin@parksight.local").strip()
        admin_pw = os.getenv("PARKSIGHT_ADMIN_PASSWORD", "ChangeMeInProduction!").strip()
        op_email = os.getenv("PARKSIGHT_OPERATOR_EMAIL", "").strip()
        op_pw = os.getenv("PARKSIGHT_OPERATOR_PASSWORD", "").strip()

        session.add(
            APIUser(
                email=admin_email,
                hashed_password=hash_password(admin_pw),
                role="admin",
            )
        )
        if op_email and op_pw:
            session.add(
                APIUser(
                    email=op_email,
                    hashed_password=hash_password(op_pw),
                    role="operator",
                )
            )
        session.commit()
    finally:
        session.close()


async def get_current_user_optional(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
) -> UserOut:
    """When auth is off, still honor Bearer JWT for /auth/me and role checks if a token is sent."""
    hdr = request.headers.get("Authorization")
    if hdr:
        try:
            return parse_authorization_header(hdr)
        except AuthError as e:
            if _require_auth_enabled():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=str(e),
                    headers={"WWW-Authenticate": "Bearer"},
                ) from e
    if not _require_auth_enabled():
        return UserOut(id=0, email="anonymous", role="admin")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return parse_authorization_header(f"Bearer {token}")
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def require_user(user: UserOut = Depends(get_current_user_optional)) -> UserOut:
    return user


async def require_admin(user: UserOut = Depends(require_user)) -> UserOut:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    return user
