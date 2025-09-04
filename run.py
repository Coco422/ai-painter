#!/usr/bin/env python3
"""
AI Painter 启动脚本
"""

import os
import sys
import uvicorn
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """启动应用"""
    # 设置环境变量
    os.environ.setdefault("SECRET_KEY", "dev-secret-key-change-in-production")
    os.environ.setdefault("DEBUG", "true")
    os.environ.setdefault("PORT", "8000")
    os.environ.setdefault("DATABASE_URL", "sqlite:///./aipainter.db")
    os.environ.setdefault("ADMIN_USERNAME", "admin")
    os.environ.setdefault("ADMIN_EMAIL", "admin@example.com")
    os.environ.setdefault("ADMIN_PASSWORD", "admin123")

    # 开发环境配置
    if os.getenv("DEBUG", "false").lower() == "true":
        print("🚀 启动开发服务器...")
        uvicorn.run(
            "backend.main:app",
            host="0.0.0.0",
            port=int(os.getenv("PORT", 8000)),
            reload=True,
            reload_dirs=[str(project_root / "backend")]
        )
    else:
        print("🚀 启动生产服务器...")
        uvicorn.run(
            "backend.main:app",
            host="0.0.0.0",
            port=int(os.getenv("PORT", 8000)),
            workers=4
        )

if __name__ == "__main__":
    main()
