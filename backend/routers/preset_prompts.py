from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.database import get_db, User, PresetPrompt
from ..models.schemas import PresetPromptCreate, PresetPromptUpdate, PresetPromptResponse, APIResponse
from ..auth.security import get_current_user, get_current_admin_user

router = APIRouter(prefix="/preset-prompts", tags=["preset-prompts"])

@router.get("/", response_model=List[PresetPromptResponse])
def get_preset_prompts(
    prompt_type: Optional[str] = Query(None, description="提示词类型过滤 (text2img, img2img, both)"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=100, description="返回数量"),
    db: Session = Depends(get_db)
):
    """获取预设提示词列表（公开接口）"""
    query = db.query(PresetPrompt).filter(
        and_(
            PresetPrompt.is_active == True,
            PresetPrompt.is_deleted == False
        )
    )
    
    if prompt_type:
        query = query.filter(
            (PresetPrompt.prompt_type == prompt_type) | 
            (PresetPrompt.prompt_type == "both")
        )
    
    preset_prompts = query.offset(skip).limit(limit).all()
    return preset_prompts

@router.get("/{prompt_id}", response_model=PresetPromptResponse)
def get_preset_prompt(prompt_id: int, db: Session = Depends(get_db)):
    """获取单个预设提示词详情"""
    preset_prompt = db.query(PresetPrompt).filter(
        and_(
            PresetPrompt.id == prompt_id,
            PresetPrompt.is_active == True,
            PresetPrompt.is_deleted == False
        )
    ).first()
    
    if not preset_prompt:
        raise HTTPException(status_code=404, detail="预设提示词不存在")
    
    return preset_prompt

@router.post("/", response_model=PresetPromptResponse)
def create_preset_prompt(
    preset_data: PresetPromptCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """创建预设提示词（仅管理员）"""
    # 验证prompt_type
    if preset_data.prompt_type not in ["text2img", "img2img", "both"]:
        raise HTTPException(
            status_code=400, 
            detail="提示词类型必须是 text2img, img2img 或 both"
        )
    
    preset_prompt = PresetPrompt(
        prompt_content=preset_data.prompt_content,
        example_image_url=preset_data.example_image_url,
        prompt_source=preset_data.prompt_source,
        prompt_type=preset_data.prompt_type,
        created_by=current_user.id
    )
    
    db.add(preset_prompt)
    db.commit()
    db.refresh(preset_prompt)
    
    return preset_prompt

@router.put("/{prompt_id}", response_model=PresetPromptResponse)
def update_preset_prompt(
    prompt_id: int,
    preset_data: PresetPromptUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """更新预设提示词（仅管理员）"""
    preset_prompt = db.query(PresetPrompt).filter(PresetPrompt.id == prompt_id).first()
    
    if not preset_prompt:
        raise HTTPException(status_code=404, detail="预设提示词不存在")
    
    # 更新字段
    update_data = preset_data.dict(exclude_unset=True)
    
    # 验证prompt_type
    if "prompt_type" in update_data:
        if update_data["prompt_type"] not in ["text2img", "img2img", "both"]:
            raise HTTPException(
                status_code=400, 
                detail="提示词类型必须是 text2img, img2img 或 both"
            )
    
    for field, value in update_data.items():
        setattr(preset_prompt, field, value)
    
    db.commit()
    db.refresh(preset_prompt)
    
    return preset_prompt

@router.delete("/{prompt_id}", response_model=APIResponse)
def delete_preset_prompt(
    prompt_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """删除预设提示词（软删除，仅管理员）"""
    preset_prompt = db.query(PresetPrompt).filter(PresetPrompt.id == prompt_id).first()
    
    if not preset_prompt:
        raise HTTPException(status_code=404, detail="预设提示词不存在")
    
    # 软删除
    preset_prompt.is_deleted = True
    preset_prompt.is_active = False
    
    db.commit()
    
    return APIResponse(
        success=True,
        message="预设提示词删除成功"
    )

@router.post("/{prompt_id}/restore", response_model=APIResponse)
def restore_preset_prompt(
    prompt_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """恢复已删除的预设提示词（仅管理员）"""
    preset_prompt = db.query(PresetPrompt).filter(PresetPrompt.id == prompt_id).first()
    
    if not preset_prompt:
        raise HTTPException(status_code=404, detail="预设提示词不存在")
    
    # 恢复
    preset_prompt.is_deleted = False
    preset_prompt.is_active = True
    
    db.commit()
    
    return APIResponse(
        success=True,
        message="预设提示词恢复成功"
    )

@router.get("/admin/all", response_model=List[PresetPromptResponse])
def get_all_preset_prompts(
    include_deleted: bool = Query(False, description="是否包含已删除的"),
    prompt_type: Optional[str] = Query(None, description="提示词类型过滤"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=200, description="返回数量"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """获取所有预设提示词（包含已删除，仅管理员）"""
    query = db.query(PresetPrompt)
    
    if not include_deleted:
        query = query.filter(PresetPrompt.is_deleted == False)
    
    if prompt_type:
        query = query.filter(
            (PresetPrompt.prompt_type == prompt_type) | 
            (PresetPrompt.prompt_type == "both")
        )
    
    preset_prompts = query.offset(skip).limit(limit).all()
    return preset_prompts