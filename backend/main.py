from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn
import os
from pathlib import Path

from .models.database import engine, create_tables
from .routers import auth, users, generation, preset_prompts

# 创建数据库表
create_tables()

# 创建FastAPI应用
app = FastAPI(
    title="AI Painter API",
    description="AI绘画工具后端API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置为具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 获取项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 挂载静态文件
static_path = BASE_DIR / "frontend" / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# 配置模板
templates_path = BASE_DIR / "frontend" / "templates"
if templates_path.exists():
    templates = Jinja2Templates(directory=str(templates_path))

# 注册路由
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(generation.router)
app.include_router(preset_prompts.router)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """根路径返回前端页面"""
    if templates:
        return templates.TemplateResponse("index.html", {"request": request})
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Painter</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            .container { max-width: 600px; margin: 0 auto; }
            h1 { color: #ff6b35; }
            .btn { background: #ff6b35; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎨 AI Painter</h1>
            <p>AI绘画工具后端API</p>
            <p><a href="/docs" class="btn">📚 API文档</a></p>
            <p><a href="/redoc" class="btn">🔄 交互文档</a></p>
        </div>
    </body>
    </html>
    """)

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    """管理员面板"""
    if templates:
        return templates.TemplateResponse("admin.html", {"request": request})
    return HTMLResponse("管理员面板需要模板支持")

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "version": "1.0.0"}

# 处理Chrome DevTools相关请求
@app.get("/.well-known/appspecific/{path:path}")
async def handle_well_known(path: str):
    """处理Chrome DevTools相关请求，返回204避免404日志"""
    return HTMLResponse(status_code=204)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True if os.getenv("DEBUG", "false").lower() == "true" else False
    )
