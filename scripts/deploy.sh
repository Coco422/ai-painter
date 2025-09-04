#!/bin/bash

# AI Painter 部署脚本

echo "🚀 开始部署 AI Painter..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 未安装"
    exit 1
fi

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 未安装"
    exit 1
fi

# 创建虚拟环境
echo "📦 创建虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 安装依赖
echo "📦 安装依赖..."
pip install -r requirements.txt

# 初始化数据库
echo "🗄️ 初始化数据库..."
python backend/init_db.py

# 创建必要的目录
mkdir -p logs
mkdir -p uploads

echo "✅ 部署完成！"
echo ""
echo "启动应用："
echo "  source venv/bin/activate"
echo "  python run.py"
echo ""
echo "或直接运行："
echo "  source venv/bin/activate"
echo "  uvicorn backend.main:app --reload"
echo ""
echo "应用将在 http://localhost:8000 启动"
echo "API文档: http://localhost:8000/docs"
echo "管理员面板: http://localhost:8000/admin"
