# AI 科创平台 - 项目文档

## 📋 项目概述

AI 科创平台是一个面向 AI 研究者和学习者的在线教育平台，提供项目展示、学习、实验和协作功能。平台采用单页应用（SPA）架构，使用原生 JavaScript 实现，无需框架依赖。

## 📁 项目文件结构

```
AI-/
├── index.html                      # HTML 结构文件（615行）
├── app.js                          # JavaScript 核心逻辑（5774行）
├── styles.css                      # CSS 样式文件（2860行）
├── project-structure-config.js     # 项目结构配置系统（260行）
├── README.md                       # 项目文档（本文件）
├── workflow.md                     # 协作开发工作流程文档
└── PROJECT_CREATION_ENHANCEMENT_PLAN.md  # 出题功能完善计划文档
```

### 文件功能说明

| 文件 | 功能 | 行数 | 说明 |
|------|------|------|------|
| `index.html` | HTML结构 | 615 | 定义页面结构、视图、模态框等 |
| `app.js` | JavaScript逻辑 | 5774 | 包含所有业务逻辑、视图管理、数据管理等 |
| `styles.css` | CSS样式 | 2860 | 包含所有样式定义、主题变量、响应式设计 |
| `project-structure-config.js` | 配置系统 | 260 | 项目结构配置，定义章节、渲染器等 |
| `workflow.md` | 工作流程 | 407 | 协作开发规范和工作流程 |
| `PROJECT_CREATION_ENHANCEMENT_PLAN.md` | 功能计划 | 1091 | 出题功能的详细设计文档 |

---

## 🎨 UI 配置详解

### 1. 字体配置

#### 1.1 主字体
- **字体名称**: Inter
- **来源**: Google Fonts
- **引入位置**: `index.html` 第 9 行
- **字体权重**: 400, 500, 600, 700, 800

```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
```

#### 1.2 字体族设置
- **主字体**: `'Inter'`
- **备用字体**: `ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial`
- **中文字体**: `"Noto Sans", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei"`
- **配置位置**: `styles.css` 第 33 行

```css
font-family: 'Inter', ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Noto Sans", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
```

#### 1.3 代码字体
- **字体**: `'Monaco', 'Menlo', 'Ubuntu Mono', monospace`
- **使用位置**: 代码块、Notebook 代码单元格

### 2. 颜色系统

#### 2.1 CSS 变量定义
所有颜色通过 CSS 变量统一管理，位于 `styles.css` 第 1-24 行。

#### 2.2 明亮主题（默认）

```css
:root {
  --brand: #A0522D;        /* 品牌色：温暖褐红色 */
  --brand-600: #8B4513;    /* 品牌色深色：深褐色 */
  --brand-700: #6B3410;    /* 品牌色更深：更深褐色 */
  --bg: #F5F1EA;           /* 背景色：米色 */
  --bg-elev: #FFFBF5;      /* 背景色提升：奶白色 */
  --text: #3E2723;         /* 文字色：深褐色 */
  --text-2: #6D4C41;       /* 文字色次要：中褐色 */
  --muted: #EFE9E0;        /* 静音色：浅米色 */
  --border: #D7CCC8;       /* 边框色：浅褐色 */
  --card: #FFFBF5;         /* 卡片色：卡片白色 */
  --shadow: 0 2px 10px rgba(62,39,35,.08);  /* 阴影 */
}
```

#### 2.3 暗色主题

```css
.theme-dark {
  --bg: #0f1115;           /* 深色背景 */
  --bg-elev: #141821;      /* 深色背景提升 */
  --text: #e9edf4;         /* 浅色文字 */
  --text-2: #a6b0c2;       /* 浅色文字次要 */
  --muted: #242a36;        /* 深色静音 */
  --border: #1e2431;       /* 深色边框 */
  --card: #141821;          /* 深色卡片 */
  --shadow: 0 4px 20px rgba(0,0,0,.35);  /* 深色阴影 */
}
```

#### 2.4 如何修改颜色

**修改品牌色**：
1. 打开 `styles.css`
2. 找到第 2-4 行的品牌色变量
3. 修改 `--brand`、`--brand-600`、`--brand-700` 的值

**修改背景色**：
1. 修改 `--bg`（主背景色）
2. 修改 `--bg-elev`（卡片、输入框等提升的背景色）

**修改文字颜色**：
1. 修改 `--text`（主要文字颜色）
2. 修改 `--text-2`（次要文字颜色）

**修改暗色主题**：
1. 找到 `.theme-dark` 选择器（第 15-24 行）
2. 修改对应的变量值

### 3. 标题样式配置

#### 3.1 Hero 标题（首页大标题）

**配置位置**: `styles.css` 第 250-252 行

```css
.hero__title {
  margin: 0;
  font-size: clamp(40px, 6vw, 64px);  /* 响应式字体大小 */
  font-weight: 800;                    /* 超粗体 */
  line-height: 1.1;                    /* 行高 */
  color: #3E2723;                      /* 深褐色 */
}

.hero__title-prefix {
  display: block;
  font-size: clamp(20px, 2.2vw, 26px); /* 前缀字体大小 */
  color: #A0522D;                       /* 品牌色 */
  letter-spacing: 1.2px;                /* 字间距 */
  margin-bottom: 8px;
}
```

**如何修改**：
- 修改字体大小：调整 `clamp()` 函数中的值
- 修改颜色：修改 `color` 属性
- 修改字重：修改 `font-weight` 值（可选：400, 500, 600, 700, 800）

#### 3.2 页面标题

**配置位置**: `styles.css` 第 962 行

```css
.projects-heading {
  display: block;
  font-size: 28px;
  font-weight: 800;
  margin-bottom: 24px;
  color: var(--text);
}
```

#### 3.3 文章标题

**配置位置**: `styles.css` 第 664 行

```css
.article__title {
  margin: 0;
  font-size: 18px;
}
```

### 4. 按钮样式配置

#### 4.1 主要按钮（Primary Button）

**配置位置**: `styles.css` 第 377-378 行

```css
.btn--primary {
  background: linear-gradient(135deg, #CD853F 0%, #A0522D 100%);  /* 渐变背景 */
  color: #fff;                      /* 白色文字 */
  border: none;                     /* 无边框 */
  box-shadow: 0 12px 25px rgba(160, 82, 45, 0.22);  /* 阴影 */
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.btn--primary:hover {
  transform: translateY(-2px);       /* 悬停时上移 */
  box-shadow: 0 16px 32px rgba(160, 82, 45, 0.25);  /* 增强阴影 */
}
```

#### 4.2 次要按钮（Secondary Button）

**配置位置**: `styles.css` 第 278-279 行

```css
.btn--secondary {
  background: rgba(255, 251, 245, 0.8);
  border: 1px solid rgba(160, 82, 45, 0.25);
  color: #A0522D;
  /* ... */
}
```

#### 4.3 幽灵按钮（Ghost Button）

**配置位置**: `styles.css` 第 380-397 行

```css
.btn--ghost {
  background: transparent;          /* 透明背景 */
  border-color: var(--border);
  width: fit-content;
  padding: 6px 10px;
  font-size: 13px;
  border-radius: 8px;
  color: var(--text-2);
  border: none;
}
```

### 5. 主题切换

#### 5.1 切换机制
- **切换按钮**: `#themeToggle`、`#themeToggle2`、`#themeToggle3`
- **实现方式**: 切换 `theme-light` 和 `theme-dark` 类名
- **配置位置**: `app.js` 第 35-39 行

```javascript
const themeToggles = [qs('#themeToggle'), qs('#themeToggle2')].filter(Boolean);
themeToggles.forEach(btn => btn.addEventListener('click', () => {
  document.body.classList.toggle('theme-dark');
  document.body.classList.toggle('theme-light');
}));
```

#### 5.2 如何添加新的主题
1. 在 `styles.css` 中添加新的主题类（如 `.theme-blue`）
2. 定义对应的 CSS 变量
3. 在 JavaScript 中添加切换逻辑

### 6. 响应式设计

#### 6.1 断点设置

**配置位置**: `styles.css` 多处媒体查询

```css
/* 超宽屏 */
@media (min-width: 1600px) { /* ... */ }

/* 大屏 */
@media (min-width: 1200px) { /* ... */ }

/* 平板 */
@media (max-width: 1200px) { /* ... */ }
@media (max-width: 900px) { /* ... */ }

/* 手机 */
@media (max-width: 680px) { /* ... */ }
```

#### 6.2 响应式字体

使用 `clamp()` 函数实现响应式字体大小：

```css
font-size: clamp(40px, 6vw, 64px);
/* 最小值 40px，理想值 6vw，最大值 64px */
```

---

## 📄 文件详解

### 1. `index.html` - HTML 结构文件

#### 1.1 整体结构
- **文档类型**: HTML5
- **语言**: 中文（zh-CN）
- **字体**: Inter（Google Fonts）
- **主题**: 支持明暗主题切换

#### 1.2 主要视图（Views）

##### 1.2.1 首页视图 (`#home-view`)
- **布局**: 1:8 比例（侧边栏:主内容区）
- **组件**:
  - **侧边栏** (`aside.sidebar`):
    - 品牌标识（AI 科创平台）
    - 主题切换按钮 (`#themeToggle`)
    - 主导航菜单 (`nav.sidebar__nav`)
    - 个人中心 (`div.sidebar__profile`)
  - **主内容区** (`main.content`):
    - Hero 区域 (`#homeHero`) - 包含标题和登录/注册按钮
    - 项目展示区 (`#projectsView`) - 项目卡片网格 (`#projectsGrid`)

##### 1.2.2 详情页视图 (`#detail-view`)
- **布局**: 1:4:4 比例（侧边栏:中间内容:右侧面板）
- **组件**:
  - **左侧边栏**: 品牌标识、返回按钮、详情页导航菜单、代码语言选择器
  - **中间内容区**: 面包屑导航、视频演示区、文章内容
  - **右侧面板**: QA Agent 聊天界面

##### 1.2.3 出题页面视图 (`#create-view`)
- **布局**: 1:8 比例（侧边栏:主内容区）
- **组件**: 出题表单、动态章节编辑器

#### 1.3 模态框（Modals）
- **登录模态框** (`#loginModal`): 角色选择
- **注册模态框** (`#registerModal`): 用户注册表单
- **文件查看模态框** (`#filesModal`): 显示 AI Agent 生成的文件
- **审核模态框** (`#adminReviewModal`): 管理员审核题目
- **小频道引导模态框** (`#channelsOnboardingModal`): 四步引导流程

### 2. `app.js` - JavaScript 核心逻辑

#### 2.1 代码结构概览

```javascript
(function () {
  // 1. DOM 工具函数
  // 2. DOM 元素选择器
  // 3. 全局变量和状态
  // 4. 主题切换
  // 5. 动画效果模块
  // 6. 视图管理模块
  // 7. 项目数据和管理
  // 8. Notebook 功能模块
  // 9. 详情页渲染模块
  // 10. 登录/注册模块
  // 11. QA Agent 模块
  // 12. 文件管理模块
  // 13. 划词工具栏模块
  // 14. 路由管理
  // 15. 出题功能模块
  // 16. 审核功能模块
  // 17. 初始化代码
})();
```

#### 2.2 核心模块

##### 2.2.1 渲染器注册表（RendererRegistry）
- **位置**: `app.js` 第 567-637 行
- **功能**: 将章节类型映射到对应的渲染函数
- **支持的渲染器**: `notebook`, `quiz`, `comments`, `custom`

##### 2.2.2 数据管理模块
- **位置**: `app.js` 第 640-741 行
- **功能**: 管理项目和分类数据，支持 localStorage 持久化
- **存储键**: `ai_platform_projects`

##### 2.2.3 Notebook 功能模块
- **位置**: `app.js` 第 1004-1469 行
- **功能**: 交互式笔记本，支持代码执行、Markdown 渲染
- **单元格类型**: `code`, `markdown`, `table`

##### 2.2.4 详情页渲染模块
- **位置**: `app.js` 第 1500-2100 行（估算）
- **功能**: 根据配置动态渲染项目详情页的各个章节

##### 2.2.5 出题功能模块（ProblemCreation）
- **位置**: `app.js` 第 3000-4500 行（估算）
- **功能**: 动态生成出题表单，收集项目数据

##### 2.2.6 审核功能模块（AdminReview）
- **位置**: `app.js` 第 5400-5762 行
- **功能**: 管理员审核待发布的题目

### 3. `styles.css` - CSS 样式文件

#### 3.1 CSS 变量系统（第1-24行）
- 定义明亮和暗色主题的所有颜色变量
- 使用 `var(--variable-name)` 引用变量

#### 3.2 布局系统
- **视图布局**: Grid 布局，响应式设计
- **侧边栏布局**: Flexbox 和 Grid 混合使用

#### 3.3 组件样式
- **导航菜单**: 第 118-135 行
- **卡片样式**: 第 408-416 行
- **模态框样式**: 第 886-909 行
- **Notebook 样式**: 第 979-1046 行
- **QA Agent 样式**: 第 786-821 行
- **出题表单样式**: 第 1195-1284 行
- **审核功能样式**: 第 1296-1444 行

### 4. `project-structure-config.js` - 项目结构配置

#### 4.1 功能
- 定义项目详情页的所有章节结构
- 配置章节类型、默认内容、渲染器映射
- 支持配置版本管理

#### 4.2 章节类型
- `notebook`: Notebook 格式章节
- `quiz`: 个性化检验（选择题）
- `comments`: 留言区
- `custom`: 自定义渲染器

#### 4.3 配置方法
- 修改 `sections` 数组添加新章节
- 更新 `defaultCells` 修改默认内容
- 调整 `order` 改变章节顺序

---

## 🚀 快速开始

### 本地运行

```bash
# 启动本地服务器
python3 -m http.server 8000

# 或使用 Node.js
npx http-server -p 8000

# 访问
http://localhost:8000
```

### 浏览器支持
- Chrome/Edge（推荐）
- Firefox
- Safari

---

## 🎯 功能模块

### 1. 项目展示
- 项目卡片网格展示
- 分类筛选
- 项目详情页

### 2. 交互式笔记本
- 代码单元格（支持 Python、JavaScript 等）
- Markdown 单元格
- 表格单元格
- 代码执行（模拟）

### 3. 出题功能
- 动态表单生成
- Notebook 编辑器
- 个性化检验编辑器
- 数据收集和提交

### 4. 审核功能
- 待审核题目列表
- 批准/拒绝操作
- 审核历史记录

### 5. QA Agent
- 文献检索
- 科研建议
- 文件生成和查看

### 6. 用户系统
- 角色登录（企业、教师、用户、管理员）
- 用户注册
- 权限控制

---

## 🔧 开发指南

### 修改 UI 颜色

1. **修改品牌色**：
   - 打开 `styles.css`
   - 找到 `:root` 选择器（第 1 行）
   - 修改 `--brand`、`--brand-600`、`--brand-700` 的值

2. **修改背景色**：
   - 修改 `--bg`（主背景）
   - 修改 `--bg-elev`（卡片背景）

3. **修改文字颜色**：
   - 修改 `--text`（主文字）
   - 修改 `--text-2`（次要文字）

### 修改字体

1. **修改主字体**：
   - 修改 `styles.css` 第 33 行的 `font-family`
   - 如需使用新字体，在 `index.html` 中引入字体文件

2. **修改代码字体**：
   - 查找 `.cell-input`、`.code-block code` 等选择器
   - 修改 `font-family` 属性

### 修改标题样式

1. **Hero 标题**：
   - 修改 `styles.css` 第 250-252 行的 `.hero__title`

2. **页面标题**：
   - 修改 `.projects-heading`（第 962 行）
   - 修改 `.article__title`（第 664 行）

### 添加新章节

1. 打开 `project-structure-config.js`
2. 在 `sections` 数组中添加新章节配置
3. 配置章节的 `key`、`name`、`type`、`order` 等属性
4. 如需自定义渲染，在 `RendererRegistry` 中注册渲染器

---

## 📝 更新日志

### v1.0.0 (2024-01-XX)
- ✨ 初始版本发布
- ✨ 交互式笔记本功能
- ✨ 项目管理系统
- ✨ 出题和审核功能
- ✨ AI Agent 集成
- ✨ 用户角色系统
- ✨ 明暗主题切换
- ✨ 响应式设计

---

## 🐛 已知问题

- [ ] 代码执行环境为模拟实现，实际项目中需要后端支持
- [ ] 文件上传功能尚未实现
- [ ] 审核历史记录未保存
- [ ] 移动端适配需要进一步优化

---

## 🔮 未来计划

- [ ] 后端 API 集成
- [ ] 真实的代码执行环境
- [ ] 用户认证系统
- [ ] 数据可视化
- [ ] 协作功能
- [ ] 导出功能（PDF、Markdown）
- [ ] 搜索功能
- [ ] 通知系统

---

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证

---

## 👥 贡献者

- **wangmingxuan**: 项目主框架、详情页、QA Agent、Notebook 等功能
- **zhaoziwei**: "我要出题"功能模块、管理员审核模块、项目结构配置系统

---

## 📧 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 Issue
- 发送邮件

---

**⭐ 如果这个项目对您有帮助，请给个 Star！**
