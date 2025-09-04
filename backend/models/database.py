from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
import os

# 数据库配置 - 支持SQLite和PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aipainter.db")

# 创建引擎 - 根据URL自动选择数据库类型
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    invite_code = Column(String(20), nullable=True)  # 注册时使用的邀请码（管理员可以为空）
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    points = Column(Integer, default=0)  # 积分数量
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    generations = relationship("Generation", back_populates="user")
    redemptions = relationship("Redemption", back_populates="user")
    created_templates = relationship("PromptTemplate", back_populates="creator")
    favorite_templates = relationship("UserFavoriteTemplate", back_populates="user")

class InviteCode(Base):
    """邀请码表"""
    __tablename__ = "invite_codes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String(20), unique=True, index=True, nullable=False)
    is_used = Column(Boolean, default=False)
    used_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # 可选的过期时间

    # 关系
    creator = relationship("User", foreign_keys=[created_by])
    user = relationship("User", foreign_keys=[used_by])

class RedemptionCode(Base):
    """兑换码表"""
    __tablename__ = "redemption_codes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    points = Column(Integer, nullable=False)  # 兑换码包含的积分
    is_used = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    used_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # 过期时间

    # 关系
    creator = relationship("User", foreign_keys=[created_by])
    user = relationship("User", foreign_keys=[used_by])
    redemptions = relationship("Redemption", back_populates="code")

class Redemption(Base):
    """兑换记录表"""
    __tablename__ = "redemptions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    code_id = Column(Integer, ForeignKey("redemption_codes.id"), nullable=False)
    points_redeemed = Column(Integer, nullable=False)
    redeemed_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    user = relationship("User", back_populates="redemptions")
    code = relationship("RedemptionCode", back_populates="redemptions")

class Generation(Base):
    """生图记录表"""
    __tablename__ = "generations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    prompt = Column(Text, nullable=False)  # 原始提示词
    optimized_prompt = Column(Text)  # 优化后的提示词
    model = Column(String(100), nullable=False)  # 使用的模型
    image_url = Column(String(500))  # 生成的图片URL
    base64_image = Column(Text)  # Base64编码的图片数据
    points_used = Column(Integer, default=1)  # 消耗的积分
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text)  # 错误信息
    api_response = Column(Text)  # API原始响应
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # 关系
    user = relationship("User", back_populates="generations")

class ApiConfig(Base):
    """API配置表"""
    __tablename__ = "api_configs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    config_key = Column(String(50), unique=True, nullable=False)  # 配置键，如 'openai', 'default'
    api_key = Column(String(500), nullable=False)
    api_base_url = Column(String(200), default="https://api.openai.com")
    optimizer_model = Column(String(100), default="gpt-4o-mini")
    system_prompt = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# 预设提示词表
class PresetPrompt(Base):
    """预设提示词表"""
    __tablename__ = "preset_prompts"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    prompt_content = Column(Text, nullable=False)                    # 提示词内容
    example_image_url = Column(String(500), nullable=True)           # 提示词案例图
    prompt_source = Column(String(100), nullable=True)               # 提示词来源
    prompt_type = Column(String(50), nullable=False)                 # 提示词类型（text2img, img2img, both）
    is_active = Column(Boolean, default=True)                        # 是否激活
    is_deleted = Column(Boolean, default=False)                      # 是否删除
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False) # 创建人
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # 创建时间
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    creator = relationship("User", foreign_keys=[created_by])

# 预设模板表（保留原有的）
class PromptTemplate(Base):
    """预设模板表"""
    __tablename__ = "prompt_templates"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)           # 模板名称
    description = Column(Text, nullable=True)            # 模板描述  
    category = Column(String(50), nullable=True)         # 分类（人物、风景、动漫等）
    thumbnail_url = Column(String(500), nullable=True)   # 缩略图URL
    prompt_text = Column(Text, nullable=False)           # 提示词内容
    negative_prompt = Column(Text, nullable=True)        # 负面提示词
    recommended_models = Column(Text, nullable=True)     # 推荐模型（JSON数组）
    recommended_size = Column(String(20), nullable=True) # 推荐尺寸
    is_active = Column(Boolean, default=True)            # 是否启用
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True) # 创建者ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    creator = relationship("User", back_populates="created_templates")

# 用户收藏模板表
class UserFavoriteTemplate(Base):
    """用户收藏模板表"""
    __tablename__ = "user_favorite_templates"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("prompt_templates.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    user = relationship("User", back_populates="favorite_templates")
    template = relationship("PromptTemplate")
    
    # 唯一约束
    __table_args__ = (UniqueConstraint('user_id', 'template_id', name='unique_user_template'),)

# 创建数据库表
def create_tables():
    """创建所有表"""
    Base.metadata.create_all(bind=engine)

# 获取数据库会话
def get_db():
    """依赖注入用的数据库会话生成器"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
