from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import uuid

import redis
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from .config import settings
from .db import async_session
from .models import User

router = APIRouter(prefix="/auth", tags=["auth"])

ALGO = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

_redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)


# --------------------
# helpers
# --------------------
def _hash_password(password: str) -> str:
    return pwd_context.hash(password)


def _verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def _ttl_from_exp(exp_ts: int) -> int:
    now_ts = int(datetime.now(timezone.utc).timestamp())
    return max(0, exp_ts - now_ts)


def _create_token(sub: str, minutes: int, token_type: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=minutes)
    payload = {
        "sub": sub,
        "jti": str(uuid.uuid4()),
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGO)


def _revoke_jti(jti: str, exp_ts: int) -> None:
    ttl = _ttl_from_exp(exp_ts)
    if ttl > 0:
        _redis.set(f"revoked:{jti}", "1", ex=ttl)


def _is_revoked(jti: str) -> bool:
    return _redis.exists(f"revoked:{jti}") == 1


async def _get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


def _decode_token(raw_token: str) -> dict:
    try:
        return jwt.decode(raw_token, settings.jwt_secret, algorithms=[ALGO])
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from e


async def _get_current_user_from_token(raw_token: str, session: AsyncSession) -> User:
    payload = _decode_token(raw_token)
    jti = payload.get("jti")
    sub = payload.get("sub")
    if not jti or not sub or _is_revoked(jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked or invalid")

    result = await session.execute(select(User).where(User.id == int(sub)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


def _issue_token_pair(user_id: int) -> Tuple[str, str]:
    access = _create_token(str(user_id), minutes=settings.jwt_expire_min, token_type="access")
    # refresh usually longer (e.g., 10080 min = 7 days); keep simple via 7x access time if not provided
    refresh_minutes = max(settings.jwt_expire_min * 7, settings.jwt_expire_min + 1)
    refresh = _create_token(str(user_id), minutes=refresh_minutes, token_type="refresh")
    return access, refresh


# --------------------
# endpoints
# --------------------
@router.post("/login")
async def login(form: OAuth2PasswordRequestForm = Depends()):
    async with async_session() as session:
        user = await _get_user_by_email(session, form.username)
        if not user or not _verify_password(form.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        access, refresh = _issue_token_pair(user.id)
        return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}


@router.post("/refresh")
async def refresh(refresh_token: str = Header(..., alias="X-Refresh-Token")):
    payload = _decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not a refresh token")

    if _is_revoked(payload["jti"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    # rotate: revoke old refresh jti and issue a new pair
    _revoke_jti(payload["jti"], payload["exp"])
    access, new_refresh = _issue_token_pair(int(user_id))
    return {"access_token": access, "refresh_token": new_refresh, "token_type": "bearer"}


@router.post("/logout")
async def logout(
    authorization: str = Header(..., alias="Authorization"),
    refresh_token: str = Header(..., alias="X-Refresh-Token"),
):
    # Authorization: Bearer <token>
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad Authorization header")
    access_token = authorization.replace("Bearer ", "").strip()

    # revoke both
    for raw in (access_token, refresh_token):
        payload = _decode_token(raw)
        _revoke_jti(payload["jti"], payload["exp"])
    return {"status": "ok"}


# dependency for protected routes
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    async with async_session() as session:
        return await _get_current_user_from_token(token, session)
