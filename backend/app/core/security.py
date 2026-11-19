import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2 import exceptions as argon2_exceptions
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.entities import RefreshSession, User

password_hash = PasswordHasher()
bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return password_hash.verify(hashed, password)
    except argon2_exceptions.VerificationError:
        return False


def _token(sub: str, kind: str, expires: timedelta, jti: str | None = None) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": sub,
            "type": kind,
            "iss": settings.jwt_issuer,
            "iat": now,
            "exp": now + expires,
            "jti": jti or secrets.token_urlsafe(16),
        },
        settings.jwt_secret,
        algorithm="HS256",
    )


def issue_tokens(user: User, db: Session, family_id: str | None = None) -> dict:
    access = _token(str(user.id), "access", timedelta(minutes=settings.access_token_minutes))
    raw_refresh = secrets.token_urlsafe(48)
    db.add(
        RefreshSession(
            user_id=user.id,
            family_id=family_id or secrets.token_hex(16),
            token_hash=hashlib.sha256(raw_refresh.encode()).hexdigest(),
            expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_days),
        )
    )
    db.commit()
    refresh_jwt = _token(
        str(user.id),
        "refresh",
        timedelta(days=settings.refresh_token_days),
        jti=raw_refresh,
    )
    return {
        "access_token": access,
        "refresh_token": refresh_jwt,
        "token_type": "bearer",  # nosec B105
        "expires_in": settings.access_token_minutes * 60,
    }


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentification requise",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not credentials:
        raise unauthorized
    try:
        claims = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=["HS256"],
            issuer=settings.jwt_issuer,
            options={"require": ["exp", "iat", "sub", "type"]},
        )
        if claims.get("type") != "access":
            raise unauthorized
        user = db.get(User, int(claims["sub"]))
        if not user or not user.is_active:
            raise unauthorized
        return user
    except (jwt.PyJWTError, ValueError, TypeError):
        raise unauthorized from None


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé à l’administration")
    return user
