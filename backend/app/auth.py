import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlmodel import Session, select

from .db import get_session
from .models import User, Role

# =====================================================
# ✅ CONFIG
# =====================================================
SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MIN", "60"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
router = APIRouter(prefix="/auth", tags=["Auth"])

# =====================================================
# ✅ SCHEMAS
# =====================================================
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserPublic(BaseModel):
    id: int
    email: str
    role: Optional[str]

    class Config:
        orm_mode = True


# =====================================================
# ✅ UTILS
# =====================================================
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Создает JWT токен"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# =====================================================
# ✅ DEPENDENCIES
# =====================================================
async def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    """Извлекает пользователя по JWT"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await session.exec(select(User).where(User.email == email))
    user = user.first()
    if not user:
        raise credentials_exception
    return user


def has_role(required_role: str):
    """Dependency для проверки роли пользователя"""
    async def role_checker(current_user: User = Depends(get_current_user)):
        if not current_user.role:
            raise HTTPException(status_code=403, detail="User has no role assigned")
        if current_user.role.name != required_role:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient role: required '{required_role}'"
            )
        return current_user
    return role_checker


# =====================================================
# ✅ ROUTES
# =====================================================
@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    """Авторизация пользователя и выдача токена"""
    result = await session.exec(select(User).where(User.email == form_data.username))
    user = result.first()
    if not user or user.hashed_password != form_data.password:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    token_data = {"sub": user.email}
    token = create_access_token(token_data)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserPublic)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Получение текущего пользователя"""
    return UserPublic(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role.name if current_user.role else None,
    )
