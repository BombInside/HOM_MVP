from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Header # EN: Added Header for token access
# EN: Added Redis for revocation list
# RU: Добавлен Redis для списка отзыва
import redis
import json
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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login") 

# ----------------------------------------------------
# EN: Redis client setup for Token Revocation List
# RU: Настройка клиента Redis для Списка Отзыва Токенов
# ----------------------------------------------------
# EN: Use decode_responses=True to get strings instead of bytes
# RU: Используем decode_responses=True для получения строк вместо байтов
redis_client = redis.from_url(settings.redis_url, decode_responses=True)

async def get_session() -> AsyncSession:
    async with async_session() as s:
        yield s

def hash_password(p: str) -> str:
    return pwd_context.hash(p)

def verify_password(plain, hashed) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(sub: str, minutes: int):
    exp = datetime.now(timezone.utc) + timedelta(minutes=minutes) # EN: Use timezone.utc for consistency
    to_encode = {"sub": sub, "exp": exp.timestamp()} # EN: Use timestamp for JOSE
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=ALGO)

# EN: Function to add a token to the blacklist with its remaining expiry time
# RU: Функция для добавления токена в черный список с оставшимся сроком действия
def revoke_token(token: str):
    try:
        # EN: Decode without verification to get expiry time
        # RU: Декодируем без верификации для получения времени истечения
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGO], options={"verify_signature": False})
        
        token_id = token # EN: Using the token itself as the ID for simplicity
        exp_timestamp = payload.get("exp")
        
        if exp_timestamp is None:
            return False # EN: Cannot revoke token without expiry
            
        # EN: Calculate time to live (TTL) in seconds
        # RU: Вычисляем время жизни (TTL) в секундах
        ttl = max(0, int(exp_timestamp - datetime.now(timezone.utc).timestamp()))
        
        if ttl > 0:
            # EN: Add token ID to Redis blacklist set with the calculated expiry
            # RU: Добавляем ID токена в черный список Redis с вычисленным сроком истечения
            redis_client.set(token_id, "revoked", ex=ttl) 
            return True
        return False
    except (JWTError, Exception) as e:
        print(f"Token revocation error: {e}")
        return False

# EN: Function to check if a token is in the blacklist
# RU: Функция для проверки, находится ли токен в черном списке
def is_token_revoked(token: str) -> bool:
    return redis_client.exists(token) == 1

# ----------------------------------------------------
# EN: JWT Dependency with Revocation Check
# RU: Зависимость JWT с проверкой отзыва
# ----------------------------------------------------
async def get_current_user(
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme)
) -> User:
    # EN: 💡 CRITICAL: Check if the token is revoked FIRST
    # RU: 💡 КРИТИЧЕСКИ: Проверяем, отозван ли токен ПЕРВЫМ ДЕЛОМ
    if is_token_revoked(token):
        raise HTTPException(status_code=401, detail="Token revoked")
        
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGO])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials (No subject)")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    # EN: Fetch user from DB (code simplified for brevity)
    # RU: Получаем пользователя из БД (код упрощен для краткости)
    user_q = await session.execute(select(User).where(User.id == int(user_id)))
    user = user_q.scalar_one_or_none()
    
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
        
    return user 

# ... (has_role, RequiresRole remain the same) ...

@router.post("/login")
async def login(form: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_session)):
    # ... (логика без изменений) ...
    q = await session.execute(select(User).where(User.email == form.username))
    user = q.scalar_one_or_none()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        
    access = create_token(str(user.id), settings.jwt_expire_min)
    refresh = create_token(str(user.id), settings.jwt_expire_min * 24)
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}

@router.post("/refresh")
async def refresh(token: str = Header(..., alias="Authorization")): # EN: Get token from Authorization header
    # EN: Strip 'Bearer ' prefix if present
    # RU: Удаляем префикс 'Bearer ', если он присутствует
    token = token.replace("Bearer ", "") 
    
    # 💡 EN: CRITICAL: Check if the token is revoked
    # 💡 RU: КРИТИЧЕСКИ: Проверяем, отозван ли токен
    if is_token_revoked(token):
        raise HTTPException(status_code=401, detail="Token revoked")
        
    try:
        # EN: Decode to check expiry and subject
        # RU: Декодируем для проверки срока действия и субъекта
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGO])
        sub = payload.get("sub")
        if not sub:
            raise ValueError
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    # EN: Revoke old token immediately after generating a new one (optional, but good practice)
    # RU: Отзываем старый токен сразу после генерации нового (опционально, но хорошая практика)
    revoke_token(token) 
    
    return {"access_token": create_token(sub, settings.jwt_expire_min)}

# ----------------------------------------------------
# EN: New endpoint for user logout
# RU: Новый эндпоинт для выхода пользователя
# ----------------------------------------------------
@router.post("/logout")
async def logout(
    access_token: str = Header(..., alias="Authorization"),
    refresh_token: str = Header(..., alias="X-Refresh-Token") # EN: Assuming refresh token is passed in a custom header
):
    # EN: Extract raw token string
    # RU: Извлекаем чистую строку токена
    access_token = access_token.replace("Bearer ", "")
    
    # EN: Revoke both tokens
    # RU: Отзываем оба токена
    if not revoke_token(access_token) or not revoke_token(refresh_token):
        raise HTTPException(status_code=400, detail="One or both tokens could not be revoked.")
        
    return {"status": "success", "message": "Logged out successfully"}