from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime
import random
import string

from ..models.database import User, RedemptionCode, Redemption, Generation, InviteCode, ApiConfig
from ..models.schemas import UserCreate, UserUpdate, UserResponse, RedemptionCodeResponse, RedeemCodeResponse, InviteCodeResponse, ApiConfigCreate, ApiConfigUpdate, ApiConfigResponse
from ..auth.security import get_password_hash

class UserService:
    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """创建新用户"""
        # 检查用户名是否已存在
        if db.query(User).filter(User.username == user_data.username).first():
            raise HTTPException(status_code=400, detail="用户名已存在")

        # 验证邀请码（管理员用户不需要邀请码）
        invite_code_obj = None
        if user_data.invite_code:
            invite_code_obj = db.query(InviteCode).filter(
                InviteCode.code == user_data.invite_code,
                InviteCode.is_used == False
            ).first()

            if not invite_code_obj:
                raise HTTPException(status_code=400, detail="邀请码无效或已被使用")

            # 检查邀请码是否过期
            if invite_code_obj.expires_at and invite_code_obj.expires_at < datetime.utcnow():
                raise HTTPException(status_code=400, detail="邀请码已过期")
        else:
            # 检查是否已有其他用户（如果是第一个用户，允许不使用邀请码）
            user_count = db.query(User).count()
            if user_count > 0:
                raise HTTPException(status_code=400, detail="需要有效的邀请码才能注册")

        # 创建用户
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            username=user_data.username,
            hashed_password=hashed_password,
            invite_code=user_data.invite_code
        )

        try:
            # 如果使用了邀请码，标记为已使用
            if invite_code_obj:
                invite_code_obj.is_used = True
                invite_code_obj.used_by = db_user.id  # 会在commit后设置
                invite_code_obj.used_at = datetime.utcnow()

            db.add(db_user)
            db.commit()
            db.refresh(db_user)

            # 更新邀请码的used_by字段
            if invite_code_obj:
                invite_code_obj.used_by = db_user.id
                db.commit()

            return db_user
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="用户创建失败")

    @staticmethod
    def update_user(db: Session, user_id: int, user_data: UserUpdate, current_user: User) -> User:
        """更新用户信息"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # 检查权限（只有管理员或自己可以修改）
        if not current_user.is_admin and current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Not enough permissions")

        # 更新字段
        update_data = user_data.dict(exclude_unset=True)
        if 'password' in update_data:
            update_data['hashed_password'] = get_password_hash(update_data.pop('password'))

        for field, value in update_data.items():
            setattr(user, field, value)

        try:
            db.commit()
            db.refresh(user)
            return user
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Update failed")

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User:
        """根据ID获取用户"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    @staticmethod
    def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """获取用户列表"""
        return db.query(User).offset(skip).limit(limit).all()

    @staticmethod
    def deactivate_user(db: Session, user_id: int, current_user: User):
        """逻辑删除用户"""
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Not enough permissions")

        user = UserService.get_user_by_id(db, user_id)
        user.is_active = False
        db.commit()

    @staticmethod
    def generate_redemption_code(db: Session, points: int, created_by: int, expires_at=None) -> str:
        """生成兑换码"""
        # 生成唯一兑换码
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
            if not db.query(RedemptionCode).filter(RedemptionCode.code == code).first():
                break

        # 创建兑换码记录
        redemption_code = RedemptionCode(
            code=code,
            points=points,
            created_by=created_by,
            expires_at=expires_at
        )

        db.add(redemption_code)
        db.commit()
        db.refresh(redemption_code)
        return code

    @staticmethod
    def redeem_code(db: Session, code: str, user_id: int) -> RedeemCodeResponse:
        """使用兑换码"""
        # 查找兑换码
        redemption_code = db.query(RedemptionCode).filter(RedemptionCode.code == code).first()
        if not redemption_code:
            raise HTTPException(status_code=404, detail="Invalid redemption code")

        # 检查是否已使用
        if redemption_code.is_used:
            raise HTTPException(status_code=400, detail="Code has already been used")

        # 检查是否过期
        if redemption_code.expires_at and redemption_code.expires_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Code has expired")

        # 检查用户是否存在
        user = UserService.get_user_by_id(db, user_id)

        try:
            # 标记兑换码为已使用
            redemption_code.is_used = True
            redemption_code.used_by = user_id
            redemption_code.used_at = datetime.utcnow()

            # 增加用户积分
            user.points += redemption_code.points

            # 创建兑换记录
            redemption = Redemption(
                user_id=user_id,
                code_id=redemption_code.id,
                points_redeemed=redemption_code.points
            )

            db.add(redemption)
            db.commit()

            return RedeemCodeResponse(
                success=True,
                message="Code redeemed successfully",
                points_added=redemption_code.points,
                total_points=user.points
            )

        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Redemption failed")

    @staticmethod
    def get_redemption_codes(db: Session, created_by: Optional[int] = None) -> List[RedemptionCode]:
        """获取兑换码列表"""
        query = db.query(RedemptionCode)
        if created_by:
            query = query.filter(RedemptionCode.created_by == created_by)
        return query.all()

    @staticmethod
    def deduct_points(db: Session, user_id: int, points: int = 1) -> bool:
        """扣除用户积分"""
        user = UserService.get_user_by_id(db, user_id)
        if user.points < points:
            raise HTTPException(status_code=400, detail="Insufficient points")

        user.points -= points
        db.commit()
        return True

    @staticmethod
    def add_points(db: Session, user_id: int, points: int) -> bool:
        """增加用户积分"""
        user = UserService.get_user_by_id(db, user_id)
        user.points += points
        db.commit()
        return True

    @staticmethod
    def generate_invite_code(db: Session, created_by: int, expires_at=None) -> str:
        """生成邀请码"""
        # 生成唯一邀请码
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not db.query(InviteCode).filter(InviteCode.code == code).first():
                break

        # 创建邀请码记录
        invite_code = InviteCode(
            code=code,
            created_by=created_by,
            expires_at=expires_at
        )

        db.add(invite_code)
        db.commit()
        db.refresh(invite_code)
        return code

    @staticmethod
    def get_invite_codes(db: Session, created_by: Optional[int] = None) -> List[InviteCode]:
        """获取邀请码列表"""
        query = db.query(InviteCode)
        if created_by:
            query = query.filter(InviteCode.created_by == created_by)
        return query.order_by(InviteCode.created_at.desc()).all()

    @staticmethod
    def validate_invite_code(db: Session, code: str) -> bool:
        """验证邀请码是否有效"""
        invite_code = db.query(InviteCode).filter(
            InviteCode.code == code,
            InviteCode.is_used == False
        ).first()

        if not invite_code:
            return False

        # 检查是否过期
        if invite_code.expires_at and invite_code.expires_at < datetime.utcnow():
            return False

        return True

    @staticmethod
    def get_user_stats(db: Session, user_id: int):
        """获取用户统计信息"""
        user = UserService.get_user_by_id(db, user_id)

        # 获取生图历史
        generations = db.query(Generation).filter(
            Generation.user_id == user_id
        ).order_by(Generation.created_at.desc()).limit(10).all()

        # 统计总数
        total_generations = db.query(Generation).filter(
            Generation.user_id == user_id,
            Generation.status == "completed"
        ).count()

        return {
            "user": user,
            "recent_generations": generations,
            "total_generations": total_generations
        }

    @staticmethod
    def get_redeem_codes(db: Session) -> List[RedemptionCode]:
        """获取所有兑换码"""
        return db.query(RedemptionCode).order_by(RedemptionCode.created_at.desc()).all()

    @staticmethod
    def create_api_config(db: Session, config_data: ApiConfigCreate) -> ApiConfig:
        """创建API配置"""
        # 检查配置键是否已存在
        if db.query(ApiConfig).filter(ApiConfig.config_key == config_data.config_key).first():
            raise HTTPException(status_code=400, detail="配置键已存在")

        config = ApiConfig(
            config_key=config_data.config_key,
            api_key=config_data.api_key,
            api_base_url=config_data.api_base_url,
            optimizer_model=config_data.optimizer_model,
            system_prompt=config_data.system_prompt,
            is_active=True
        )

        db.add(config)
        db.commit()
        db.refresh(config)
        return config

    @staticmethod
    def get_api_configs(db: Session) -> List[ApiConfig]:
        """获取所有API配置"""
        return db.query(ApiConfig).order_by(ApiConfig.created_at.desc()).all()

    @staticmethod
    def get_active_api_config(db: Session) -> Optional[ApiConfig]:
        """获取激活的API配置"""
        return db.query(ApiConfig).filter(ApiConfig.is_active == True).first()

    @staticmethod
    def update_api_config(db: Session, config_key: str, config_data: ApiConfigUpdate) -> ApiConfig:
        """更新API配置"""
        config = db.query(ApiConfig).filter(ApiConfig.config_key == config_key).first()
        if not config:
            raise HTTPException(status_code=404, detail="配置不存在")

        # 更新字段
        update_data = config_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(config, field, value)

        config.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(config)
        return config

    @staticmethod
    def delete_api_config(db: Session, config_key: str):
        """删除API配置"""
        config = db.query(ApiConfig).filter(ApiConfig.config_key == config_key).first()
        if not config:
            raise HTTPException(status_code=404, detail="配置不存在")

        db.delete(config)
        db.commit()
