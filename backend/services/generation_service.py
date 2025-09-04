import httpx
import json
import base64
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException
import os
from datetime import datetime

from ..models.database import Generation, User, ApiConfig
from ..models.schemas import GenerationRequest, GenerationResponse
from .user_service import UserService

class GenerationService:
    def __init__(self):
        # 默认值，后续可通过请求参数覆盖
        self.default_api_base_url = os.getenv("AI_API_BASE_URL", "https://api.openai.com")
        self.default_api_key = os.getenv("AI_API_KEY", "")

    async def optimize_prompt(self, prompt: str, optimizer_model: str = "gpt-4o-mini", api_key: str = None, api_base_url: str = None, system_prompt: str = None) -> str:
        """使用AI优化提示词"""
        # 使用提供的参数或默认值
        final_api_key = api_key or self.default_api_key
        final_api_base_url = api_base_url or self.default_api_base_url

        if not final_api_key:
            return prompt  # 如果没有API密钥，直接返回原提示词

        if not system_prompt:
            system_prompt = """你是一个专业的AI绘画提示词优化专家。请将用户输入的中文描述优化并翻译成高质量的英文绘画提示词。要求：1.保持原意不变 2.增加艺术性描述 3.使用专业绘画术语 4.直接返回优化后的英文提示词，不要解释过程"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{final_api_base_url}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {final_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": optimizer_model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 500,
                        "temperature": 0.7
                    },
                    timeout=30.0
                )

                if response.status_code == 200:
                    result = response.json()
                    optimized = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    return optimized if optimized else prompt
                else:
                    print(f"Prompt optimization failed: {response.status_code}")
                    return prompt

        except Exception as e:
            print(f"Prompt optimization error: {str(e)}")
            return prompt

    async def generate_image(
        self,
        db: Session,
        user_id: int,
        request: GenerationRequest
    ) -> List[Generation]:
        """生成图像（支持多模型）"""
        # 检查用户积分
        user = UserService.get_user_by_id(db, user_id)
        if user.points < 1:
            raise HTTPException(status_code=400, detail="积分不足")

        # 获取激活的API配置
        api_config = UserService.get_active_api_config(db)
        if not api_config:
            raise HTTPException(status_code=500, detail="系统API配置未设置，请联系管理员")

        # 如果请求中没有指定优化器配置，使用数据库中的默认配置
        final_optimizer_model = request.optimizer_model or api_config.optimizer_model
        final_system_prompt = request.system_prompt or api_config.system_prompt

        # 优化提示词（根据开关决定是否启用）
        optimized_prompt = ""
        if request.enable_optimization and final_optimizer_model and final_system_prompt:
            optimized_prompt = await self.optimize_prompt(
                request.prompt,
                final_optimizer_model,
                api_config.api_key,
                api_config.api_base_url,
                final_system_prompt
            )
        else:
            optimized_prompt = request.prompt

        generations = []

        # 为每个模型创建生成记录
        for model in request.models:
            generation = Generation(
                user_id=user_id,
                prompt=request.prompt,
                optimized_prompt=optimized_prompt if optimized_prompt != request.prompt else None,
                model=model,
                points_used=1,
                status="processing"
            )

            db.add(generation)
            generations.append(generation)

        db.commit()

        # 为每个生成记录刷新数据
        for generation in generations:
            db.refresh(generation)

        try:
            # 为每个模型并发生成图像
            for i, generation in enumerate(generations):
                try:
                    # 调用AI API生成图像
                    image_result = await self._call_ai_api(request, optimized_prompt, generation.model, api_config)

                    # 更新生成记录
                    if image_result.get("success"):
                        generation.status = "completed"
                        generation.image_url = image_result.get("image_url")
                        generation.base64_image = image_result.get("base64_image")
                        generation.api_response = json.dumps(image_result.get("raw_response", {}))
                        generation.completed_at = datetime.utcnow()
                    else:
                        generation.status = "failed"
                        generation.error_message = image_result.get("error", "Unknown error")

                except Exception as e:
                    generation.status = "failed"
                    generation.error_message = str(e)

            # 计算成功的生成数量
            successful_generations = sum(1 for gen in generations if gen.status == "completed")
            
            # 扣除积分：基础生成1分 + 若启用提示词优化再扣1分
            points_to_deduct = 1
            if request.enable_optimization:
                points_to_deduct += 1
            
            # 只有至少有一个成功时才扣除积分
            if successful_generations > 0:
                UserService.deduct_points(db, user_id, points_to_deduct)
                # 更新每个生成记录的积分使用情况
                for generation in generations:
                    if generation.status == "completed":
                        generation.points_used = points_to_deduct  # 成功的记录标记积分消耗
                    else:
                        generation.points_used = 0  # 失败的记录不消耗积分
            else:
                # 所有生成都失败，不扣除积分
                for generation in generations:
                    generation.points_used = 0
                    
            db.commit()

        except Exception as e:
            # 如果整体失败，标记所有记录为失败，不扣除积分
            for generation in generations:
                generation.status = "failed"
                generation.error_message = str(e)
                generation.points_used = 0  # 失败不消耗积分
            db.commit()

        return generations

    async def _call_ai_api(self, request: GenerationRequest, optimized_prompt: str, model: str, api_config: ApiConfig) -> Dict[str, Any]:
        """调用AI API生成图像"""
        try:
            # 使用数据库中的API配置
            final_api_key = api_config.api_key
            final_api_base_url = api_config.api_base_url

            payload = {
                "prompt": optimized_prompt,
                "model": model,
                "n": 1,
                "size": request.size,
                "output_format": request.output_format
            }

            headers = {
                "Authorization": f"Bearer {final_api_key}",
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient() as client:
                if request.image_file:
                    # 图片编辑模式
                    endpoint = f"{final_api_base_url}/v1/images/edits"

                    # 将base64转换为文件对象
                    files = {
                        "image": ("image.png", base64.b64decode(request.image_file), "image/png")
                    }
                    data = {
                        "prompt": optimized_prompt,
                        "model": model,
                        "n": 1,
                        "size": request.size
                    }

                    response = await client.post(
                        endpoint,
                        headers={"Authorization": f"Bearer {final_api_key}"},
                        files=files,
                        data=data,
                        timeout=60.0
                    )
                else:
                    # 图片生成模式
                    endpoint = f"{final_api_base_url}/v1/images/generations"
                    response = await client.post(
                        endpoint,
                        headers=headers,
                        json=payload,
                        timeout=60.0
                    )

                if response.status_code == 200:
                    result = response.json()

                    # 处理不同API的响应格式
                    image_data = self._extract_image_data(result)
                    if image_data:
                        return {
                            "success": True,
                            "image_url": image_data.get("url"),
                            "base64_image": image_data.get("b64_json"),
                            "raw_response": result
                        }
                    else:
                        return {
                            "success": False,
                            "error": "No image data in response"
                        }
                else:
                    error_text = response.text
                    try:
                        error_json = response.json()
                        error_text = error_json.get("error", {}).get("message", error_text)
                    except:
                        pass

                    return {
                        "success": False,
                        "error": f"API call failed: {response.status_code} - {error_text}"
                    }

        except Exception as e:
            return {
                "success": False,
                "error": f"API call error: {str(e)}"
            }

    def _extract_image_data(self, response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从API响应中提取图片数据"""
        data = response.get("data", [])
        if not data:
            return None

        item = data[0] if isinstance(data, list) else data

        # 尝试不同的图片数据字段
        if "b64_json" in item:
            return {"b64_json": item["b64_json"]}
        elif "url" in item:
            return {"url": item["url"]}
        elif "image_url" in item:
            return {"url": item["image_url"]}

        return None

    def get_generation_history(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> Dict[str, Any]:
        """获取用户的生成历史"""
        generations = db.query(Generation).filter(
            Generation.user_id == user_id
        ).order_by(Generation.created_at.desc()).offset(skip).limit(limit).all()

        total_count = db.query(Generation).filter(
            Generation.user_id == user_id
        ).count()

        return {
            "generations": generations,
            "total_count": total_count
        }

    def delete_generations(
        self,
        db: Session,
        user_id: int,
        generation_ids: List[int]
    ) -> bool:
        """删除指定的生成记录"""
        try:
            # 只允许用户删除自己的记录
            deleted_count = db.query(Generation).filter(
                Generation.id.in_(generation_ids),
                Generation.user_id == user_id
            ).delete(synchronize_session=False)
            
            db.commit()
            return deleted_count > 0
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

    def clear_user_generations(
        self,
        db: Session,
        user_id: int
    ) -> bool:
        """清空用户的所有生成记录"""
        try:
            deleted_count = db.query(Generation).filter(
                Generation.user_id == user_id
            ).delete(synchronize_session=False)
            
            db.commit()
            return deleted_count > 0
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"清空失败: {str(e)}")
