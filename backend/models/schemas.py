from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# 用户相关模型
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str
    invite_code: Optional[str] = None

class UserUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    points: Optional[int] = None

class UserResponse(UserBase):
    id: int
    invite_code: Optional[str] = None
    is_active: bool
    is_admin: bool
    points: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# 邀请码相关模型
class InviteCodeCreate(BaseModel):
    expires_at: Optional[datetime] = None

class InviteCodeResponse(BaseModel):
    id: int
    code: str
    is_used: bool
    used_by: Optional[int] = None
    created_by: int
    created_at: datetime
    used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# 认证相关模型
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

# 兑换码相关模型
class RedemptionCodeCreate(BaseModel):
    points: int
    expires_at: Optional[datetime] = None

class RedemptionCodeResponse(BaseModel):
    id: int
    code: str
    points: int
    is_used: bool
    created_by: int
    used_by: Optional[int] = None
    used_at: Optional[datetime] = None
    created_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class RedeemCodeRequest(BaseModel):
    code: str

class RedeemCodeResponse(BaseModel):
    success: bool
    message: str
    points_added: int
    total_points: int

# 生图相关模型
class GenerationRequest(BaseModel):
    prompt: str
    enable_optimization: bool = True  # 是否启用提示词优化
    models: List[str]  # 支持多模型
    size: str = "1024x1024"
    output_format: str = "png"
    image_file: Optional[str] = None  # Base64编码的图片文件
    optimizer_model: Optional[str] = None  # 提示词优化模型
    system_prompt: Optional[str] = None  # 系统提示词

class ApiConfigCreate(BaseModel):
    """API配置创建模型"""
    config_key: str
    api_key: str
    api_base_url: str = "https://api.openai.com"
    optimizer_model: Optional[str] = "gpt-4o-mini"
    system_prompt: Optional[str] = None

class ApiConfigUpdate(BaseModel):
    """API配置更新模型"""
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    optimizer_model: Optional[str] = None
    system_prompt: Optional[str] = None
    is_active: Optional[bool] = None

class ApiConfigResponse(BaseModel):
    """API配置响应模型"""
    id: int
    config_key: str
    api_key: str  # 注意：实际使用时应该隐藏或加密
    api_base_url: str
    optimizer_model: Optional[str]
    system_prompt: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# 预设提示词相关模型
class PresetPromptCreate(BaseModel):
    """创建预设提示词请求模型"""
    prompt_content: str
    example_image_url: Optional[str] = None
    prompt_source: Optional[str] = None
    prompt_type: str  # text2img, img2img, both

class PresetPromptUpdate(BaseModel):
    """更新预设提示词请求模型"""
    prompt_content: Optional[str] = None
    example_image_url: Optional[str] = None
    prompt_source: Optional[str] = None
    prompt_type: Optional[str] = None
    is_active: Optional[bool] = None
    is_deleted: Optional[bool] = None

class PresetPromptResponse(BaseModel):
    """预设提示词响应模型"""
    id: int
    prompt_content: str
    example_image_url: Optional[str]
    prompt_source: Optional[str]
    prompt_type: str
    is_active: bool
    is_deleted: bool
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# 预设模板相关模型
class PromptTemplateCreate(BaseModel):
    """创建预设模板请求模型"""
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    thumbnail_url: Optional[str] = None
    prompt_text: str
    negative_prompt: Optional[str] = None
    recommended_models: Optional[str] = None  # JSON字符串
    recommended_size: Optional[str] = None

class PromptTemplateUpdate(BaseModel):
    """更新预设模板请求模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    thumbnail_url: Optional[str] = None
    prompt_text: Optional[str] = None
    negative_prompt: Optional[str] = None
    recommended_models: Optional[str] = None
    recommended_size: Optional[str] = None
    is_active: Optional[bool] = None

class PromptTemplateResponse(BaseModel):
    """预设模板响应模型"""
    id: int
    name: str
    description: Optional[str]
    category: Optional[str]
    thumbnail_url: Optional[str]
    prompt_text: str
    negative_prompt: Optional[str]
    recommended_models: Optional[str]
    recommended_size: Optional[str]
    is_active: bool
    created_by: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class GenerationResponse(BaseModel):
    id: int
    prompt: str
    optimized_prompt: Optional[str] = None
    model: str
    image_url: Optional[str] = None
    base64_image: Optional[str] = None
    status: str
    points_used: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

class GenerationHistoryResponse(BaseModel):
    generations: List[GenerationResponse]
    total_count: int
    current_points: int

# API响应模型
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

class UserInfoResponse(BaseModel):
    user: UserResponse
    recent_generations: List[GenerationResponse]
    total_generations: int
