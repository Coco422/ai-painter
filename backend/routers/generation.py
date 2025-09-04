from typing import List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..models.database import get_db, User
from ..models.schemas import GenerationRequest, GenerationResponse, GenerationHistoryResponse
from ..auth.security import get_current_user
from ..services.generation_service import GenerationService

class DeleteGenerationsRequest(BaseModel):
    generation_ids: List[int]

router = APIRouter(prefix="/generation", tags=["generation"])
generation_service = GenerationService()

@router.post("/generate", response_model=List[GenerationResponse])
async def generate_image(
    request: GenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """生成图像（支持多模型）"""
    generations = await generation_service.generate_image(db, current_user.id, request)

    return [
        GenerationResponse(
            id=gen.id,
            prompt=gen.prompt,
            optimized_prompt=gen.optimized_prompt,
            model=gen.model,
            image_url=gen.image_url,
            base64_image=gen.base64_image,
            status=gen.status,
            points_used=gen.points_used,
            created_at=gen.created_at,
            completed_at=gen.completed_at,
            error_message=gen.error_message
        )
        for gen in generations
    ]

@router.get("/history", response_model=GenerationHistoryResponse)
def get_generation_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取生图历史"""
    result = generation_service.get_generation_history(db, current_user.id, skip, limit)

    generations = []
    for gen in result["generations"]:
        generations.append(GenerationResponse(
            id=gen.id,
            prompt=gen.prompt,
            optimized_prompt=gen.optimized_prompt,
            model=gen.model,
            image_url=gen.image_url,
            base64_image=gen.base64_image,
            status=gen.status,
            points_used=gen.points_used,
            created_at=gen.created_at,
            completed_at=gen.completed_at,
            error_message=gen.error_message
        ))

    return GenerationHistoryResponse(
        generations=generations,
        total_count=result["total_count"],
        current_points=current_user.points
    )

@router.get("/models")
def get_available_models():
    """获取可用的AI模型列表"""
    # 这里可以根据实际支持的模型动态返回
    models = [
        {"id": "gpt-4o-image", "name": "GPT-4o Image", "description": "OpenAI GPT-4o图像生成"},
        {"id": "dall-e-3", "name": "DALL-E 3", "description": "OpenAI DALL-E 3"},
        {"id": "dall-e-2", "name": "DALL-E 2", "description": "OpenAI DALL-E 2"},
        {"id": "stable-diffusion", "name": "Stable Diffusion", "description": "开源图像生成模型"},
        {"id": "midjourney", "name": "Midjourney", "description": "Midjourney风格生成"}
    ]
    return {"models": models}

@router.get("/sizes")
def get_available_sizes():
    """获取可用的图像尺寸"""
    sizes = [
        {"id": "1024x1024", "name": "正方形", "description": "1024x1024 (1:1)"},
        {"id": "1024x1792", "name": "竖屏", "description": "1024x1792 (9:16)"},
        {"id": "1792x1024", "name": "横屏", "description": "1792x1024 (16:9)"},
        {"id": "512x512", "name": "小尺寸", "description": "512x512 (快速生成)"},
        {"id": "1024x768", "name": "宽屏", "description": "1024x768 (4:3)"}
    ]
    return {"sizes": sizes}

@router.get("/formats")
def get_available_formats():
    """获取可用的输出格式"""
    formats = [
        {"id": "png", "name": "PNG", "description": "无损压缩，适合透明背景"},
        {"id": "jpeg", "name": "JPEG", "description": "有损压缩，文件更小"},
        {"id": "webp", "name": "WebP", "description": "现代格式，压缩率高"}
    ]
    return {"formats": formats}

@router.delete("/delete")
def delete_generations(
    request: DeleteGenerationsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除指定的生成记录"""
    if not request.generation_ids:
        raise HTTPException(status_code=400, detail="请选择要删除的记录")
    
    success = generation_service.delete_generations(db, current_user.id, request.generation_ids)
    if success:
        return {"message": f"成功删除 {len(request.generation_ids)} 条记录"}
    else:
        raise HTTPException(status_code=404, detail="没有找到可删除的记录")

@router.delete("/clear")
def clear_generations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """清空用户的所有生成记录"""
    success = generation_service.clear_user_generations(db, current_user.id)
    if success:
        return {"message": "历史记录已清空"}
    else:
        return {"message": "没有记录需要清空"}
