# 🎨 AI Painter

一个现代化的AI绘画工具，具有用户管理系统、积分兑换机制和JWT认证。

## ✨ 特性

- 🔐 **用户认证系统** - 基于JWT的安全认证
- 🎯 **积分管理系统** - 1积分=1次生图
- 🎁 **兑换码系统** - 管理员生成，用户兑换积分
- 🎨 **AI图像生成** - 支持多种AI模型
- 📱 **现代化界面** - 响应式设计，简约美观
- 👥 **管理员功能** - 用户管理、兑换码生成
- 📊 **历史记录** - 完整的生成历史追踪

## 🚀 快速开始

### 环境要求

- Python 3.8+
- pip

### 安装依赖

```bash
pip install -r requirements.txt
```

### 初始化数据库

```bash
# 初始化数据库和创建管理员账户
python backend/init_db.py
```

### 启动应用

```bash
# 开发模式
python run.py

# 或者直接运行
uvicorn backend.main:app --reload
```

应用将在 http://localhost:8000 启动

### 默认管理员账户

- 用户名: `admin`
- 密码: `admin123`
- 积分: `1000`

### 🎫 邀请码系统
- 注册需要有效的邀请码
- 管理员可以生成邀请码
- 普通用户也可以生成邀请码
- 支持邀请码过期时间设置

#### 示例邀请码
- `KFJBZ756` - 永久有效
- `276TYTSY` - 2025-10-02过期
- `Q5PGUSP8` - 2025-12-01过期

## 📁 项目结构

```
aipainter/
├── backend/                    # 后端代码
│   ├── models/                # 数据模型
│   │   ├── database.py       # 数据库配置和模型
│   │   └── schemas.py        # Pydantic模型
│   ├── routers/              # API路由
│   │   ├── auth.py          # 认证相关
│   │   ├── users.py         # 用户管理
│   │   └── generation.py    # 图像生成
│   ├── services/            # 业务逻辑
│   │   ├── user_service.py  # 用户服务
│   │   └── generation_service.py # 生成服务
│   ├── auth/                # 认证模块
│   │   └── security.py      # JWT安全
│   └── main.py              # FastAPI应用入口
├── frontend/                # 前端代码
│   ├── templates/          # HTML模板
│   │   └── index.html      # 主页面
│   └── static/             # 静态资源
│       ├── style.css       # 样式文件
│       └── app.js          # 前端逻辑
├── requirements.txt         # Python依赖
├── run.py                  # 启动脚本
└── README.md               # 项目文档
```

## 🔧 配置

### 环境变量

创建 `.env` 文件配置以下变量：

```env
# 应用配置
SECRET_KEY=your-secret-key-here
DEBUG=true
PORT=8000

# 数据库配置
DATABASE_URL=sqlite:///./aipainter.db

# AI API 配置
AI_API_KEY=your-openai-api-key-here
AI_API_BASE_URL=https://api.openai.com

# 管理员账户
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

### 数据库迁移

项目使用KISS设计，支持SQLite和PostgreSQL：

```env
# SQLite (默认，适合开发)
DATABASE_URL=sqlite:///./aipainter.db

# PostgreSQL (生产环境推荐)
DATABASE_URL=postgresql://user:password@localhost/aipainter
```

## 📚 API 文档

启动应用后，访问：
- API文档: http://localhost:8000/docs
- 交互式文档: http://localhost:8000/redoc

### 主要API接口

#### 认证接口
- `POST /auth/register` - 用户注册
- `POST /auth/login` - 用户登录
- `GET /auth/me` - 获取当前用户信息

#### 用户管理
- `GET /users/me/info` - 获取用户完整信息
- `PUT /users/me` - 更新用户信息
- `POST /users/redeem` - 兑换积分码

#### 图像生成
- `POST /generation/generate` - 生成图像
- `GET /generation/history` - 获取生成历史

#### 管理员功能
- `GET /users/admin/users` - 获取所有用户
- `PUT /users/admin/users/{user_id}` - 更新用户信息
- `DELETE /users/admin/users/{user_id}` - 删除用户
- `POST /users/admin/redeem-codes` - 生成兑换码
- `POST /users/admin/invite-codes` - 管理员生成邀请码
- `GET /users/admin/invite-codes` - 管理员获取邀请码列表
- `GET /users/invite-codes` - 获取我的邀请码
- `POST /users/invite-codes` - 生成我的邀请码

## 🎨 前端界面

### 设计特色

- **现代化风格** - 白色背景，橙色品牌色
- **响应式布局** - 支持桌面和移动设备
- **卡片式设计** - 清晰的功能分区
- **双栏布局** - 左侧提示引擎，右侧输出画廊
- **直观交互** - 简洁的用户体验

### 主要功能

1. **用户注册登录** - 需要邀请码的安全账户管理
2. **邀请码系统** - 生成和管理邀请码
3. **积分兑换** - 使用兑换码获取积分
4. **图像生成** - 输入提示词生成AI图像
5. **图像编辑** - 上传图片进行AI编辑
6. **历史记录** - 查看生成历史和状态

## 🔒 安全特性

- JWT token认证
- 密码bcrypt加密
- API请求频率限制
- CORS配置
- 输入验证和清理

## 🚀 部署

### 生产环境部署

1. 设置环境变量
2. 配置PostgreSQL数据库
3. 设置反向代理 (nginx)
4. 配置SSL证书
5. 设置进程管理器 (systemd/supervisor)

### Docker部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📝 更新日志

### v1.1.0 - 简化注册流程重构
- ✅ **简化注册表单**: 只保留用户名、密码和邀请码字段
- ✅ **移除邮箱字段**: 不再需要邮箱验证
- ✅ **添加邀请码系统**: 实现完整的邀请码生成和验证机制
- ✅ **数据库重构**: 移除不必要的字段，优化数据结构
- ✅ **管理员功能增强**: 添加邀请码管理功能
- ✅ **API测试完善**: 完整的API自动化测试
- ✅ **用户体验优化**: 更简洁直观的注册流程

### v1.0.0 - 初始版本
- 🎨 现代化前端界面设计
- 🔐 JWT用户认证系统
- 💰 积分和兑换码管理系统
- 🎯 AI图像生成接口
- 👥 完整的管理员功能
- 📱 响应式设计支持

## 📄 许可证

MIT License

## 📞 联系方式

如有问题，请提交Issue或联系开发团队。
