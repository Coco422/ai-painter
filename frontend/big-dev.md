# AI Painter 大版本开发计划

## 核心改动

### 1. 提示词优化开关功能
- **数据库变更**: 无需变更，通过前端设置管理
- **前端**: 添加开关控件，控制是否启用提示词优化
- **后端**: 修改生成接口，根据开关决定是否调用优化服务

### 2. 界面重构：图生图/文生图模式
- **布局变更**: 参考设计图，左侧为模式选择和参数，右侧为结果展示
- **模式切换**: 实现图生图和文生图两种模式的切换
- **UI组件**: 重新设计参数面板，优化用户体验

### 3. 预设生图提示词系统
**数据库新增表**:
```sql
-- 预设模板表
CREATE TABLE prompt_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,           -- 模板名称
    description TEXT,                     -- 模板描述  
    category VARCHAR(50),                 -- 分类（人物、风景、动漫等）
    thumbnail_url VARCHAR(500),           -- 缩略图URL
    prompt_text TEXT NOT NULL,            -- 提示词内容
    negative_prompt TEXT,                 -- 负面提示词
    recommended_models TEXT,              -- 推荐模型（JSON数组）
    recommended_size VARCHAR(20),         -- 推荐尺寸
    is_active BOOLEAN DEFAULT TRUE,       -- 是否启用
    created_by INTEGER,                   -- 创建者ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 用户收藏模板表
CREATE TABLE user_favorite_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    template_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (template_id) REFERENCES prompt_templates(id),
    UNIQUE(user_id, template_id)
);
```

**后端API新增**:
- `GET /templates` - 获取预设模板列表
- `GET /templates/{id}` - 获取模板详情
- `POST /admin/templates` - 创建模板（管理员）
- `PUT /admin/templates/{id}` - 更新模板（管理员）
- `DELETE /admin/templates/{id}` - 删除模板（管理员）
- `POST /users/templates/{id}/favorite` - 收藏模板
- `DELETE /users/templates/{id}/favorite` - 取消收藏

**前端功能**:
- 模板展示网格（类似第二张图的效果）
- 分类筛选功能
- 搜索功能
- 收藏功能
- 模板预览和应用

## 实现步骤

### Phase 1: 提示词优化开关
1. 前端添加开关控件
2. 修改生成接口参数
3. 更新后端生成逻辑

### Phase 2: 界面重构
1. 重新设计HTML结构
2. 更新CSS样式
3. 修改JavaScript交互逻辑
4. 实现模式切换功能

### Phase 3: 预设模板系统
1. 创建数据库表和模型
2. 实现后端API接口
3. 开发前端模板展示组件
4. 集成模板应用功能
5. 添加管理员模板管理界面

## 技术考虑

### 数据存储
- 模板缩略图可考虑本地存储或CDN
- 提示词内容支持变量替换（如{subject}, {style}等）

### 性能优化
- 模板列表分页加载
- 缩略图懒加载
- 前端缓存常用模板

### 扩展性
- 支持用户自定义模板
- 模板导入/导出功能
- 社区模板分享（后期扩展）
