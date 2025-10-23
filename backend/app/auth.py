from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from .config import settings
from .db import async_session
from .models import User

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGO = "HS256"

async def get_session() -> AsyncSession:
    async with async_session() as s:
        yield s

def hash_password(p: str) -> str:
    return pwd_context.hash(p)

def verify_password(plain, hashed) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(sub: str, minutes: int):
    exp = datetime.utcnow() + timedelta(minutes=minutes)
    to_encode = {"sub": sub, "exp": exp}
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=ALGO)

@router.post("/login")
async def login(form: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_session)):
    q = await session.execute(select(User).where(User.email == form.username))
    user = q.scalar_one_or_none()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access = create_token(str(user.id), settings.jwt_expire_min)
    refresh = create_token(str(user.id), settings.jwt_expire_min * 24)
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}

@router.post("/refresh")
async def refresh(token: str):
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGO])
        sub = payload.get("sub")
        if not sub:
            raise ValueError
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"access_token": create_token(sub, settings.jwt_expire_min)}
