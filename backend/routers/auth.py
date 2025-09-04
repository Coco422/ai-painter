from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..models.database import get_db
from ..models.schemas import Token, UserResponse, UserCreate
from ..auth.security import authenticate_user, create_access_token, get_current_user
from ..services.user_service import UserService
from ..models.database import User

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    try:
        user = UserService.create_user(db, user_data)
        return UserResponse.from_orm(user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """用户登录"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return UserResponse.from_orm(current_user)
