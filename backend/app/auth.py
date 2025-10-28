from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
# EN: Added OAuth2PasswordBearer for token scheme definition
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer 
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

# EN: Define OAuth2 scheme to extract token from 'Authorization: Bearer <token>' header
# RU: Определяем схему OAuth2 для извлечения токена из заголовка
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login") 

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

# ----------------------------------------------------
# EN: Dependency to get the currently authenticated user
# RU: Зависимость для получения текущего аутентифицированного пользователя
# ----------------------------------------------------
async def get_current_user(
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme) # EN: Get token from header
) -> User:
    try:
        # EN: Decode JWT using secret and algorithm from settings
        # RU: Декодируем JWT, используя секрет и алгоритм из настроек
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGO])
        user_id: str = payload.get("sub")
        if user_id is None:
            # EN: Token payload missing subject
            # RU: В полезной нагрузке токена отсутствует субъект
            raise HTTPException(status_code=401, detail="Invalid authentication credentials (No subject)")
    except JWTError:
        # EN: Token signature is invalid or token is expired
        # RU: Неверная подпись токена или токен просрочен
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    # EN: Fetch user from DB
    # RU: Получаем пользователя из БД
    user_q = await session.execute(select(User).where(User.id == int(user_id)))
    user = user_q.scalar_one_or_none()
    
    if user is None:
        # EN: User ID in token does not match any user in the database
        # RU: ID пользователя в токене не соответствует ни одному пользователю в базе данных
        raise HTTPException(status_code=401, detail="User not found")
        
    # EN: Check if the user is active
    # RU: Проверяем, активен ли пользователь
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")
        
    return user # EN: Return the fully authenticated and loaded User object

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
    # ⚠️ EN: NO TOKEN REVOCATION CHECK IS PERFORMED YET! (Critical future fix)
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGO])
        sub = payload.get("sub")
        if not sub:
            raise ValueError
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"access_token": create_token(sub, settings.jwt_expire_min)}