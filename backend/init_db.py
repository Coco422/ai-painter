#!/usr/bin/env python3
"""
数据库初始化脚本
用于创建初始数据和管理员用户
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import sessionmaker
from backend.models.database import engine, User
from backend.auth.security import get_password_hash

def init_database():
    """初始化数据库"""
    from backend.models.database import create_tables
    create_tables()
    print("✅ 数据库表创建完成")

def create_admin_user():
    """创建默认管理员用户"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 检查是否已存在管理员
        admin_exists = db.query(User).filter(User.is_admin == True).first()
        if admin_exists:
            print("ℹ️ 管理员用户已存在")
            return

        # 创建管理员用户
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")

        # 检查用户名是否已被使用
        existing_user = db.query(User).filter(User.username == admin_username).first()

        if existing_user:
            print(f"⚠️ 用户名已存在: {admin_username}")
            return

        hashed_password = get_password_hash(admin_password)
        admin_user = User(
            username=admin_username,
            hashed_password=hashed_password,
            is_admin=True,
            is_active=True,
            points=1000  # 赠送初始积分
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print("✅ 管理员用户创建成功")
        print(f"   用户名: {admin_username}")
        print(f"   密码: {admin_password}")
        print("   积分: 1000")

    except Exception as e:
        print(f"❌ 创建管理员用户失败: {str(e)}")
        db.rollback()
    finally:
        db.close()

def create_sample_data():
    """创建示例数据"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 创建示例邀请码和兑换码
        from backend.models.database import RedemptionCode, PromptTemplate
        from backend.services.user_service import UserService
        from datetime import datetime, timedelta, UTC
        import json

        admin = db.query(User).filter(User.is_admin == True).first()
        if admin:
            # 生成一些示例邀请码
            invite_codes_data = [
                {"expires": None},
                {"expires": datetime.now(UTC) + timedelta(days=30)},
                {"expires": datetime.now(UTC) + timedelta(days=90)}
            ]

            print("🎫 生成示例邀请码:")
            for i, code_data in enumerate(invite_codes_data, 1):
                code = UserService.generate_invite_code(
                    db, admin.id, code_data["expires"]
                )
                expires_info = f" (过期: {code_data['expires'].strftime('%Y-%m-%d')})" if code_data["expires"] else ""
                print(f"  {i}. {code}{expires_info}")

            # 生成一些示例兑换码
            print("\n💰 生成示例兑换码:")
            codes_data = [
                {"points": 10, "expires": None},
                {"points": 50, "expires": None},
                {"points": 100, "expires": datetime.now(UTC) + timedelta(days=30)}
            ]

            for i, code_data in enumerate(codes_data, 1):
                code = UserService.generate_redemption_code(
                    db, code_data["points"], admin.id, code_data["expires"]
                )
                expires_info = f" (过期: {code_data['expires'].strftime('%Y-%m-%d')})" if code_data["expires"] else ""
                print(f"  {i}. {code} ({code_data['points']}积分){expires_info}")

            # 创建示例预设模板
            print("\n🎨 创建示例预设模板:")
            templates_data = [
                {
                    "name": "动漫风格女孩",
                    "description": "可爱的动漫风格女孩角色",
                    "category": "人物",
                    "prompt_text": "anime style, cute girl, big eyes, colorful hair, kawaii, detailed face, high quality, 4k",
                    "negative_prompt": "ugly, deformed, bad anatomy, blurry, low quality",
                    "recommended_models": json.dumps(["gpt-4o-image", "imagen-4.0-ultra-generate-preview-06-06"]),
                    "recommended_size": "1024x1024"
                },
                {
                    "name": "风景油画",
                    "description": "美丽的自然风景油画",
                    "category": "风景",
                    "prompt_text": "oil painting, beautiful landscape, mountains, lake, sunset, dramatic lighting, masterpiece",
                    "negative_prompt": "dark, gloomy, ugly, low quality",
                    "recommended_models": json.dumps(["imagen-4.0-ultra-generate-preview-06-06"]),
                    "recommended_size": "1792x1024"
                },
                {
                    "name": "科幻城市",
                    "description": "未来主义科幻城市景观",
                    "category": "科幻",
                    "prompt_text": "futuristic city, cyberpunk, neon lights, flying cars, skyscrapers, detailed architecture, high tech",
                    "negative_prompt": "old, vintage, low quality, blurry",
                    "recommended_models": json.dumps(["gpt-4o-image", "gemini-2.5-flash-image-preview"]),
                    "recommended_size": "1792x1024"
                },
                {
                    "name": "可爱宠物",
                    "description": "萌萌的小动物",
                    "category": "动物",
                    "prompt_text": "cute pet, fluffy, adorable, big eyes, soft fur, kawaii style, high detail",
                    "negative_prompt": "scary, ugly, deformed, low quality",
                    "recommended_models": json.dumps(["gpt-4o-image"]),
                    "recommended_size": "1024x1024"
                }
            ]

            for i, template_data in enumerate(templates_data, 1):
                template = PromptTemplate(
                    name=template_data["name"],
                    description=template_data["description"],
                    category=template_data["category"],
                    prompt_text=template_data["prompt_text"],
                    negative_prompt=template_data["negative_prompt"],
                    recommended_models=template_data["recommended_models"],
                    recommended_size=template_data["recommended_size"],
                    created_by=admin.id
                )
                db.add(template)
                print(f"  {i}. {template_data['name']} ({template_data['category']})")

            db.commit()

    except Exception as e:
        print(f"❌ 创建示例数据失败: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 开始初始化数据库...")
    init_database()
    create_admin_user()
    create_sample_data()
    print("🎉 数据库初始化完成！")
