import hashlib
import secrets
from datetime import UTC, datetime

import jwt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.ratelimit import hit, rate_limit, too_many
from app.core.security import (
    get_current_user,
    hash_password,
    issue_tokens,
    verify_password,
)
from app.models.entities import RefreshSession, User
from app.schemas.contracts import (
    LoginInput,
    RefreshInput,
    TokenPair,
    UserCreate,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["authentication"])
# Verified when the e-mail is unknown so response time does not reveal which accounts exist.
_DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


@router.post(
    "/register",
    response_model=TokenPair,
    status_code=201,
    dependencies=[Depends(rate_limit("register", 10, 3600))],
)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "Cette adresse e-mail est déjà utilisée")
    user = User(
        email=email,
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return issue_tokens(user, db)


@router.post(
    "/login",
    response_model=TokenPair,
    dependencies=[Depends(rate_limit("login", 20, 60))],
)
def login(payload: LoginInput, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    if not hit("login-email", hashlib.sha256(email.encode()).hexdigest()[:16], 5, 60):
        raise too_many()  # slows credential stuffing against one account
    user = db.scalar(select(User).where(User.email == email))
    ok = verify_password(payload.password, user.password_hash if user else _DUMMY_HASH)
    if not user or not ok or not user.is_active:
        raise HTTPException(401, "Identifiants invalides")
    return issue_tokens(user, db)


@router.post(
    "/refresh",
    response_model=TokenPair,
    dependencies=[Depends(rate_limit("refresh", 60, 60))],
)
def refresh(payload: RefreshInput, db: Session = Depends(get_db)):
    invalid = HTTPException(401, "Session expirée ou invalide")
    now = datetime.now(UTC)
    try:
        claims = jwt.decode(
            payload.refresh_token,
            settings.jwt_secret,
            algorithms=["HS256"],
            issuer=settings.jwt_issuer,
            options={"require": ["exp", "iat", "sub", "type", "jti"]},
        )
        if claims.get("type") != "refresh":
            raise invalid
        token_hash = hashlib.sha256(claims["jti"].encode()).hexdigest()
        session = db.scalar(select(RefreshSession).where(RefreshSession.token_hash == token_hash).with_for_update())
        if session is None:
            raise invalid
        if session.revoked_at is not None:
            # An already-rotated token came back: assume theft and revoke the whole login family.
            if session.family_id:
                db.execute(
                    update(RefreshSession)
                    .where(
                        RefreshSession.family_id == session.family_id,
                        RefreshSession.revoked_at.is_(None),
                    )
                    .values(revoked_at=now)
                )
                db.commit()
            raise invalid
        if session.expires_at.replace(tzinfo=UTC) < now:
            raise invalid
        user = db.get(User, int(claims["sub"]))
        if not user or not user.is_active:
            raise invalid
        session.revoked_at = now
        db.commit()
        return issue_tokens(user, db, family_id=session.family_id)
    except (jwt.PyJWTError, ValueError, TypeError, KeyError):
        raise invalid from None


@router.post("/logout", status_code=204)
def logout(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.execute(
        update(RefreshSession)
        .where(RefreshSession.user_id == current.id, RefreshSession.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )
    db.commit()


@router.get("/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)):
    return current
