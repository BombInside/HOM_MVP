from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
# EN: Added OAuth2PasswordBearer for token scheme definition
# RU: Добавлен OAuth2PasswordBearer для определения схемы токенов
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
    token: str = Depends(oauth2_scheme)
) -> User:
    try:
        # EN: Decode JWT using secret and algorithm from settings
        # RU: Декодируем JWT, используя секрет и алгоритм из настроек
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGO])
        user_id: str = payload.get("sub")
        if user_id is None:
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
        raise HTTPException(status_code=401, detail="User not found")
        
    # EN: Check if the user is active
    # RU: Проверяем, активен ли пользователь
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")
        
    return user 

# ----------------------------------------------------
# EN: RBAC Helper Functions
# RU: Вспомогательные функции для RBAC
# ----------------------------------------------------

# EN: Function to check if a user has a specific role
# RU: Функция для проверки наличия определенной роли у пользователя
def has_role(user: User, required_role_name: str) -> bool:
    # EN: Roles list is pre-fetched on user load
    # RU: Список ролей предварительно загружается при получении пользователя
    return any(role.name == required_role_name for role in user.roles)

# EN: Dependency to enforce a role check for FastAPI endpoints
# RU: Зависимость для принудительной проверки роли для эндпоинтов FastAPI
def RequiresRole(required_role_name: str):
    async def role_checker(current_user: User = Depends(get_current_user)):
        # EN: If user does not have the required role, raise 403 Forbidden
        # RU: Если у пользователя нет требуемой роли, вызываем 403 Forbidden
        if not has_role(current_user, required_role_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have the required role: {required_role_name}"
            )
        return current_user
    return role_checker

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
    # ⚠️ RU: ПРОВЕРКА ОТЗЫВА ТОКЕНА ЕЩЕ НЕ ВЫПОЛНЯЕТСЯ! (Критический будущий фикс)
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGO])
        sub = payload.get("sub")
        if not sub:
            raise ValueError
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"access_token": create_token(sub, settings.jwt_expire_min)}