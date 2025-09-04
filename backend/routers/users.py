from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..models.database import get_db, User
from ..models.schemas import UserResponse, UserUpdate, UserInfoResponse, RedeemCodeRequest, RedeemCodeResponse, InviteCodeResponse, RedemptionCodeResponse, ApiConfigCreate, ApiConfigUpdate, ApiConfigResponse
from ..auth.security import get_current_user, get_current_admin_user
from ..services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me/info", response_model=UserInfoResponse)
def get_user_info(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前用户的完整信息（包含历史记录和统计）"""
    stats = UserService.get_user_stats(db, current_user.id)
    return UserInfoResponse(
        user=UserResponse.from_orm(stats["user"]),
        recent_generations=[{
            "id": g.id,
            "prompt": g.prompt,
            "optimized_prompt": g.optimized_prompt,
            "model": g.model,
            "image_url": g.image_url,
            "base64_image": g.base64_image,
            "status": g.status,
            "points_used": g.points_used,
            "created_at": g.created_at,
            "completed_at": g.completed_at,
            "error_message": g.error_message
        } for g in stats["recent_generations"]],
        total_generations=stats["total_generations"]
    )

@router.get("/admin/verify", response_model=dict)
def verify_admin_access(current_user: User = Depends(get_current_admin_user)):
    """验证管理员访问权限"""
    return {
        "is_admin": True,
        "username": current_user.username,
        "message": "管理员权限验证成功"
    }

@router.put("/me", response_model=UserResponse)
def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新当前用户信息"""
    # 不允许用户自行修改管理员权限和积分
    user_data.is_admin = None
    user_data.points = None

    updated_user = UserService.update_user(db, current_user.id, user_data, current_user)
    return UserResponse.from_orm(updated_user)

@router.post("/redeem", response_model=RedeemCodeResponse)
def redeem_code(
    request: RedeemCodeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """使用兑换码"""
    return UserService.redeem_code(db, request.code, current_user.id)

@router.get("/admin/users", response_model=List[UserResponse])
def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """管理员：获取所有用户列表"""
    users = UserService.get_users(db, skip, limit)
    return [UserResponse.from_orm(user) for user in users]

@router.put("/admin/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """管理员：更新用户信息"""
    updated_user = UserService.update_user(db, user_id, user_data, current_user)
    return UserResponse.from_orm(updated_user)

@router.delete("/admin/users/{user_id}")
def deactivate_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """管理员：逻辑删除用户"""
    UserService.deactivate_user(db, user_id, current_user)
    return {"message": "User deactivated successfully"}

@router.post("/admin/redeem-codes")
def generate_redeem_code(
    points: int = Query(..., ge=1, le=1000, description="兑换码包含的积分数量"),
    expires_at: Optional[str] = Query(None, description="过期时间，格式：YYYY-MM-DD HH:MM:SS"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """管理员：生成兑换码"""
    from datetime import datetime

    expires_datetime = None
    if expires_at:
        try:
            expires_datetime = datetime.fromisoformat(expires_at.replace(' ', 'T'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")

    code = UserService.generate_redemption_code(db, points, current_user.id, expires_datetime)
    return {"code": code, "points": points, "message": "Redemption code generated successfully"}

@router.get("/admin/redeem-codes", response_model=List[RedemptionCodeResponse])
def get_redeem_codes(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """管理员：获取兑换码列表"""
    redeem_codes = UserService.get_redeem_codes(db)
    return [RedemptionCodeResponse.from_orm(code) for code in redeem_codes]

@router.post("/admin/invite-codes")
def generate_invite_code(
    expires_at: Optional[str] = Query(None, description="过期时间，格式：YYYY-MM-DD HH:MM:SS"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """管理员：生成邀请码"""
    from datetime import datetime

    expires_datetime = None
    if expires_at:
        try:
            expires_datetime = datetime.fromisoformat(expires_at.replace(' ', 'T'))
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的日期格式")

    code = UserService.generate_invite_code(db, current_user.id, expires_datetime)
    return {"code": code, "message": "邀请码生成成功"}

@router.get("/admin/invite-codes", response_model=List[InviteCodeResponse])
def get_invite_codes(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """管理员：获取邀请码列表"""
    invite_codes = UserService.get_invite_codes(db)
    return [InviteCodeResponse.from_orm(code) for code in invite_codes]

@router.get("/invite-codes", response_model=List[InviteCodeResponse])
def get_my_invite_codes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取我生成的邀请码列表"""
    invite_codes = UserService.get_invite_codes(db, current_user.id)
    return [InviteCodeResponse.from_orm(code) for code in invite_codes]

@router.post("/invite-codes")
def generate_my_invite_code(
    expires_at: Optional[str] = Query(None, description="过期时间，格式：YYYY-MM-DD HH:MM:SS"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """生成我的邀请码"""
    from datetime import datetime

    expires_datetime = None
    if expires_at:
        try:
            expires_datetime = datetime.fromisoformat(expires_at.replace(' ', 'T'))
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的日期格式")

    code = UserService.generate_invite_code(db, current_user.id, expires_datetime)
    return {"code": code, "message": "邀请码生成成功"}

@router.get("/admin/users/{user_id}")
def get_user_details(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """管理员：获取用户详情"""
    user = UserService.get_user_by_id(db, user_id)
    return {"user": UserResponse.from_orm(user)}

@router.put("/admin/users/{user_id}", response_model=UserResponse)
def update_user_admin(
    user_id: int,
    points: int = Query(None, description="用户积分"),
    is_active: bool = Query(None, description="是否激活"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """管理员：更新用户信息"""
    from ..models.schemas import UserUpdate

    # 创建更新数据
    update_data = UserUpdate()
    if points is not None:
        update_data.points = points
    if is_active is not None:
        update_data.is_active = is_active

    # 管理员可以更新积分和激活状态
    updated_user = UserService.update_user(db, user_id, update_data, current_user)
    return UserResponse.from_orm(updated_user)

# ==================== API配置管理 ====================

@router.post("/admin/api-configs", response_model=ApiConfigResponse)
def create_api_config(
    config_data: ApiConfigCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """管理员：创建API配置"""
    config = UserService.create_api_config(db, config_data)
    return ApiConfigResponse.from_orm(config)

@router.get("/admin/api-configs", response_model=List[ApiConfigResponse])
def get_api_configs(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """管理员：获取所有API配置"""
    configs = UserService.get_api_configs(db)
    return [ApiConfigResponse.from_orm(config) for config in configs]

@router.put("/admin/api-configs/{config_key}", response_model=ApiConfigResponse)
def update_api_config(
    config_key: str,
    config_data: ApiConfigUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """管理员：更新API配置"""
    config = UserService.update_api_config(db, config_key, config_data)
    return ApiConfigResponse.from_orm(config)

@router.delete("/admin/api-configs/{config_key}")
def delete_api_config(
    config_key: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """管理员：删除API配置"""
    UserService.delete_api_config(db, config_key)
    return {"message": "API配置已删除"}

@router.get("/admin/api-configs/active", response_model=Optional[ApiConfigResponse])
def get_active_api_config(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """管理员：获取激活的API配置"""
    config = UserService.get_active_api_config(db)
    return ApiConfigResponse.from_orm(config) if config else None

# ==================== 系统统计 ====================
@router.get("/admin/stats")
def get_admin_stats(current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    """系统统计：用户数、生成数、积分总量、近7日活跃、今日生成"""
    from sqlalchemy import func
    from ..models.database import User as DBUser, Generation
    from datetime import datetime, timedelta

    total_users = db.query(func.count(DBUser.id)).scalar() or 0
    total_generations = db.query(func.count(Generation.id)).scalar() or 0
    total_points = db.query(func.coalesce(func.sum(DBUser.points), 0)).scalar() or 0

    since = datetime.utcnow() - timedelta(days=7)
    active_users_7d = db.query(func.count(func.distinct(Generation.user_id))) \
        .filter(Generation.created_at >= since).scalar() or 0

    # 今日 00:00 - 明日 00:00 (UTC)
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_start = today_start + timedelta(days=1)
    today_generations = db.query(func.count(Generation.id)) \
        .filter(Generation.created_at >= today_start) \
        .filter(Generation.created_at < tomorrow_start).scalar() or 0

    return {
        "total_users": int(total_users),
        "total_generations": int(total_generations),
        "total_points": int(total_points),
        "active_users_7d": int(active_users_7d),
        "today_generations": int(today_generations)
    }
