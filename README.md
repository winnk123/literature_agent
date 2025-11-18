# AI 科创平台

> 一个现代化的 AI 科研学习平台，集成了交互式笔记本、项目管理、内容审核等功能

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Version](https://img.shields.io/badge/version-1.0.0-green.svg)

## 📖 项目简介

AI 科创平台是一个面向科研学习者的综合性平台，提供了类似 Jupyter Notebook 的交互式编辑体验，支持代码执行、Markdown 编辑、项目管理和内容审核等功能。平台采用现代化的 Web 技术栈，提供流畅的用户体验。

## ✨ 核心功能

### 🎯 交互式笔记本体验
- **代码单元格（Code Cell）**：支持 Python、JavaScript 等多种语言
- **Markdown 单元格**：支持富文本编辑和实时渲染
- **代码执行**：内置 Python 执行环境，支持状态保持
- **单元格管理**：添加、删除、移动、运行单元格

### 📚 项目管理
- **项目分类**：图像、语音、LLM、MLLM、Agent 等
- **项目详情**：背景介绍、模型架构、IDEA 引导等
- **个性化检验**：选择题形式的知识测试
- **留言区**：类似微信公众号的评论系统

### 📝 出题功能
- **表单提交**：企业/教师可提交新题目
- **数据验证**：完整的前端表单验证
- **审核流程**：管理员审核机制
- **自动发布**：审核通过后自动上线

### ⚙️ 审核系统
- **待审核列表**：查看所有待审核题目
- **批准/拒绝**：支持批准发布或拒绝（需填写原因）
- **实时同步**：审核结果实时更新到项目列表

### 🤖 AI Agent（新增代码智能体）
- **文献模式**：文献检索和推荐
- **科研模式**：科研建议和方法指导
- **代码模式**：基于 Aider AI 的代码生成、编辑和解释
  - 🎯 智能代码生成
  - ✏️ 代码编辑和优化
  - 📖 代码解释和分析
  - 🗂️ 文件管理和下载
  - 🌐 支持多种编程语言

### 👤 个人中心
- **个人主页展示**：全屏展示个人资料、研究方向、技术栈、成果等
- **动态编辑**：支持在线编辑个人主页内容，实时保存
- **角色适配**：根据用户角色（学生/企业/教师）显示不同内容
- **数据持久化**：个人主页数据自动保存到本地存储

### 🎨 用户体验
- **响应式设计**：适配桌面和移动设备
- **暗色模式**：支持明暗主题切换
- **划词工具栏**：文本标注、高亮、询问 AI
- **可折叠面板**：侧边栏、视频区、AI Agent 区
- **智能功能栏**：顶部功能栏自动隐藏，鼠标悬停显示

## 🛠️ 技术栈

### 前端技术
- **HTML5**：语义化标签，现代化结构
- **CSS3**：
  - CSS Grid 布局
  - CSS 变量（主题系统）
  - 动画和过渡效果
  - 响应式媒体查询
- **JavaScript (ES6+)**：
  - 模块化设计（IIFE）
  - 事件驱动架构
  - localStorage 数据持久化
  - DOM 操作和动态渲染

### 数据存储
- **localStorage**：客户端数据持久化
  - 项目列表
  - 待审核题目
  - 用户账号信息
  - 笔记标注

## 📁 项目结构

```
科创平台_cursor/
├── index.html                      # 主页面结构
├── styles.css                      # 样式文件
├── app.js                          # 主要逻辑
├── README.md                       # 项目说明文档
│
├── aider_service.py               # Aider AI 服务封装（新增）
├── api_server.py                  # Flask API 服务器（新增）
├── requirements_aider.txt         # Python 依赖（新增）
│
├── start_aider_service.bat        # Windows 启动脚本（新增）
├── start_aider_service.sh         # Linux/Mac 启动脚本（新增）
│
├── QUICK_START.md                 # 快速开始指南（新增）
├── AIDER_README.md                # Aider AI 技术文档（新增）
├── USAGE_GUIDE.md                 # 使用指南（新增）
├── TEST_GUIDE.md                  # 测试文档（新增）
└── IMPLEMENTATION_SUMMARY.md      # 实现总结（新增）
```

### 主要模块

#### `index.html`
- **首页视图**（`#home-view`）：项目展示、搜索、分类筛选
- **详情页视图**（`#detail-view`）：项目详情、笔记本、AI Agent
- **出题页视图**（`#create-view`）：题目创建表单
- **个人中心视图**（`#profile-view`）：个人主页展示和编辑（全屏布局）
- **模态框组件**：登录、注册、审核、文件查看、个人主页编辑、合作发起
- **功能栏**：顶部智能隐藏的功能栏

#### `styles.css`
- **主题系统**：CSS变量定义（`:root`、`.theme-dark`），深红色主题体系
- **布局系统**：Grid布局、Flexbox布局，响应式断点
- **组件样式**：卡片、按钮、表单、模态框、导航、侧边栏
- **个人中心样式**：Hero区域、信息卡片、标签云、成果列表
- **响应式设计**：媒体查询、移动端适配
- **动画效果**：过渡动画、粒子特效、扇形展开
- **交互状态**：悬停、激活、禁用状态样式

#### `app.js`
- **数据管理模块**：项目数据初始化、localStorage 管理、用户数据持久化
- **视图管理**：首页、项目、详情、出题、个人中心视图切换
- **笔记本模块**：单元格创建、渲染、执行
- **出题模块**：表单处理、数据验证、提交审核
- **审核模块**：审核列表、批准/拒绝逻辑
- **AI Agent**：问答交互、文件生成
- **用户系统**：登录、注册、角色管理
- **个人中心模块**：个人主页数据加载、渲染、编辑、保存

## 🚀 快速开始

### 方式一: 仅前端体验（无需配置）

1. **直接打开**
   ```bash
   # 在浏览器中打开 index.html
   start index.html  # Windows
   open index.html   # Mac
   ```

2. **使用代码智能体**
   - 进入任意项目详情页
   - 点击"代码"标签
   - 输入代码需求（使用模拟响应）

### 方式二: 完整功能体验（需要配置）

#### 前端部分
- 直接在浏览器中打开 `index.html`
- 或使用本地服务器：
  ```bash
  python -m http.server 8000
  ```

#### 后端部分（代码智能体）

1. **安装依赖**
   ```bash
   pip install -r requirements_aider.txt
   ```

2. **配置 API Key**
   ```bash
   # Windows
   set OPENAI_API_KEY=your-api-key-here
   
   # Linux/Mac
   export OPENAI_API_KEY=your-api-key-here
   ```

3. **启动服务**
   ```bash
   # 使用启动脚本（推荐）
   start_aider_service.bat  # Windows
   ./start_aider_service.sh  # Linux/Mac
   
   # 或手动启动
   python api_server.py
   ```

4. **访问平台**
   - 打开浏览器访问 `http://localhost:8000`
   - 或直接打开 `index.html` 文件

📖 **详细步骤请查看**: [快速开始指南](QUICK_START.md)

## 📖 使用指南

### 1. 登录系统

点击首页的"登录"按钮，选择角色：
- **企业用户**：可出题、上传数据
- **高校教师**：可出题、上传数据
- **普通使用者**：浏览学习
- **管理员**：全部权限 + 审核功能

### 2. 浏览项目

- 点击左侧导航"项目"
- 按分类筛选项目
- 点击项目卡片查看详情

### 3. 查看项目详情

项目详情页包含以下部分：
- **背景**：项目背景介绍（Notebook 格式）
- **模型**：模型架构说明
- **IDEA 引导**：优化方向建议
- **个性化检验**：知识测试
- **留言区**：评论和讨论

### 4. 使用笔记本功能

在"背景"、"模型"、"IDEA 引导"等部分：
- **编辑 Markdown**：点击文本块进入编辑模式
- **运行代码**：点击代码单元格的运行按钮
- **添加单元格**：点击"添加代码单元格"按钮
- **管理单元格**：使用工具栏按钮（上移、下移、删除）

### 5. 出题功能

1. 以企业或教师角色登录
2. 点击"出题"按钮
3. 填写表单信息：
   - 题目名称
   - 分类和子分类
   - 项目描述
   - 背景介绍（可选）
4. 提交审核
5. 等待管理员批准

### 6. 审核功能

1. 以管理员角色登录
2. 点击"审核题目"按钮
3. 查看待审核列表
4. 选择"批准发布"或"拒绝"
5. 批准的题目自动上线

### 7. AI Agent 交互

#### 文献模式
1. 在详情页右侧 AI Agent 区域
2. 选择"文献"标签
3. 输入文献检索需求
4. 查看 AI 推荐的文献

#### 科研模式
1. 选择"科研"标签
2. 输入研究问题
3. 获取研究建议和方法指导

#### 代码模式（新增）
1. 选择"代码"标签
2. 输入代码需求，例如：
   - "用 Python 写一个快速排序函数"
   - "优化这段代码的性能"
   - "解释这段代码是如何工作的"
3. 查看 AI 生成的代码
4. 点击"文件"按钮查看和下载生成的文件

📖 **详细使用方法**: [使用指南](USAGE_GUIDE.md)

### 8. 文本标注

1. 在允许的分区（背景、模型、IDEA 引导等）选择文本
2. 使用工具栏进行：
   - 高亮标注
   - 下划线
   - 删除线
   - 询问 AI

## 🎨 UI 设计规范

### 整体设计风格

平台采用**学术风格设计**（参考香港理工大学 NLP Lab 招博海报），追求：
- **学院风（Academic）**：专业、正式、学术化
- **简洁克制（Minimal）**：去除多余装饰，聚焦内容
- **高阅读体验（High Readability）**：高对比度，清晰可读
- **强结构感（Structured Layout）**：明确的视觉层级和分区

### 色彩体系

#### 核心红色色板

```css
--red-dark: #7F0037;        /* 深红 - 用于标题条、重要强调 */
--red-primary: #A5192E;     /* 主深红 - 用于按钮、主要交互 */
--red-soft: #B8404A;        /* 柔和红 - 用于标签、次要强调 */
--red-light: #FFF2F2;       /* 浅粉背景 - 用于悬浮窗、柔和区域 */
```

**使用规则**：
- ✅ 使用以上三种红色作为核心色板
- ❌ 不使用亮红、高饱和红、粉红
- ✅ 红色作为**点缀色**，背景保持浅色
- ✅ 大面积背景必须保持轻、简洁、干净

#### 中性色系统

```css
--text: #333333;            /* 主文字 - 深灰（WCAG AA） */
--text-2: #666666;         /* 次要文字 - 中灰 */
--text-3: #999999;          /* 辅助文字 - 浅灰 */
--border: #E5E5E5;          /* 浅灰色边框 */
--bg: #FAFAFA;              /* 主背景 - 极浅灰 */
--bg-elev: #FFFFFF;         /* 卡片背景 - 纯白 */
```

### 侧边栏设计规范（重点）

#### 整体结构

侧边栏采用**纯白背景**（`#FFFFFF`），学术风格设计：

```css
.sidebar {
  background: #FFFFFF;              /* 纯白背景 */
  border-right: 1px solid #E5E5E5; /* 浅灰右侧边框 */
  box-shadow: 1px 0 4px rgba(0, 0, 0, 0.04); /* 轻微阴影 */
}
```

#### 品牌区域（`.sidebar__brand`）

- **背景**：纯白 `#FFFFFF`
- **分隔线**：底部 2px 深红边框（`#7F0037`）
- **Logo**：
  - 尺寸：40px × 40px
  - 背景：深红 `#7F0037`
  - 文字：白色 `#FFFFFF`
  - 圆角：6px
  - 悬停：背景变为主深红 `#A5192E`
- **品牌名**：
  - 颜色：深红 `#7F0037`
  - 字号：16px
  - 字重：700

#### 导航区域（`.sidebar__nav`）

##### 导航标题（`.nav__title`）

```css
.nav__title {
  color: #888888;                    /* 中灰色 */
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;        /* 大写字母 */
  letter-spacing: 1.5px;
  border-bottom: 1px solid #E5E5E5; /* 浅灰下划线 */
}
```

##### 导航项（`.nav__item`）- 核心设计

**默认状态**：
```css
.nav__item {
  color: #333333;                    /* 深灰文字，高对比度 */
  background: transparent;            /* 透明背景 */
  padding: 8px 16px;                 /* 舒适的内边距 */
  border-radius: 6px;                /* 小圆角 */
  font-size: 14px;
  font-weight: 500;
  border-left: 3px solid transparent; /* 左侧边框预留 */
}
```

**悬停状态（`:hover`）**：
```css
.nav__item:hover {
  background: #FAFAFA;               /* 极浅灰背景 */
  color: #7F0037;                    /* 深红色文字 */
  border-left-color: #B8404A;        /* 左侧柔和红边框 */
  padding-left: calc(16px - 1px);    /* 补偿边框宽度 */
}
```

**激活状态（`.is-active`）**：
```css
.nav__item.is-active {
  background: #FFF2F2;               /* 浅粉背景 */
  color: #7F0037;                    /* 深红色文字 */
  font-weight: 600;                  /* 加粗 */
  border-left-color: #A5192E;        /* 左侧主深红边框 */
  padding-left: calc(16px - 1px);
}
```

##### 导航图标（`.nav__icon`）

```css
.nav__icon {
  width: 18px;
  height: 18px;
  stroke: #888888;                   /* 默认：中灰色 */
  stroke-width: 1.8;
}

.nav__item:hover .nav__icon {
  stroke: #7F0037;                   /* 悬停：深红色 */
}

.nav__item.is-active .nav__icon {
  stroke: #A5192E;                   /* 激活：主深红 */
  stroke-width: 2.2;
}
```

#### 子导航列表（`.nav__sublist`）

```css
.nav__sublist {
  border-left: 2px solid #E5E5E5;    /* 左侧浅灰边框 */
  padding-left: 24px;
  margin-left: 16px;
}

.nav__sublist .nav__item {
  color: #666666;                    /* 中灰文字 */
  font-size: 13px;
  border-left: none;                 /* 移除左侧边框 */
}

.nav__sublist .nav__item:hover {
  color: #7F0037;
  background: #FAFAFA;
}

.nav__sublist .nav__item.is-active {
  background: #FFF2F2;
  color: #7F0037;
  border-left: 2px solid #B8404A;    /* 左侧柔和红边框 */
}
```

#### 筛选组和语言选择器

```css
.filter__group,
.language-selector {
  background: #FFFFFF;                /* 白色背景 */
  border: 1px solid #E5E5E5;         /* 浅灰边框 */
  border-left: 3px solid #7F0037;     /* 左侧深红边框（强调） */
  border-radius: 8px;
  padding: 16px;
}

.filter__title,
.language-selector__title {
  color: #888888;                    /* 中灰色 */
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.check,
.language-option {
  color: #333333;                    /* 深灰文字 */
  font-size: 13px;
}

.check:hover,
.language-option:hover {
  color: #7F0037;                    /* 悬停：深红色 */
}

.check input[type="checkbox"],
.language-option input[type="checkbox"] {
  accent-color: #A5192E;            /* 主深红 */
}

.check input[type="checkbox"]:checked,
.language-option input[type="checkbox"]:checked {
  accent-color: #7F0037;            /* 选中：深红色 */
}
```

#### 个人资料区域（`.sidebar__profile`）

```css
.sidebar__profile {
  background: #FAFAFA;                /* 极浅灰背景 */
  border-top: 1px solid #E5E5E5;     /* 浅灰上边框 */
  padding: 16px;
}

.profile__avatar {
  width: 40px;
  height: 40px;
  background: #7F0037;                /* 深红背景 */
  color: #FFFFFF;                    /* 白色文字 */
  border-radius: 6px;
}

.profile__name {
  color: #333333;                    /* 深灰文字 */
  font-size: 14px;
  font-weight: 600;
}

.profile__sub {
  color: #888888;                    /* 中灰文字 */
  font-size: 12px;
}
```

#### 详情页控制按钮（`.detail__sidectrl`）

```css
.detail__sidectrl {
  background: #FFFFFF;
  border-bottom: 1px solid #E5E5E5;
  padding: 16px;
}

.detail__sidectrl .btn--ghost {
  color: #666666;                    /* 中灰文字 */
  border-color: #E5E5E5;
  background: transparent;
}

.detail__sidectrl .btn--ghost:hover {
  color: #7F0037;                    /* 深红色文字 */
  border-color: #B8404A;             /* 柔和红边框 */
  background: #FAFAFA;                /* 极浅灰背景 */
}
```

### 设计原则总结

1. **背景优先**：侧边栏使用纯白背景，确保所有文字清晰可读
2. **红色点缀**：深红色仅用于强调和交互反馈，不作为大面积背景
3. **状态明确**：通过背景色、文字色、左侧边框的组合，清晰区分默认/悬停/激活状态
4. **结构清晰**：使用分隔线、边框、间距建立明确的视觉层级
5. **高对比度**：深灰文字（`#333333`）配白色背景，符合 WCAG AA 标准

### 个人中心页面设计

#### 整体布局

个人中心页面采用**全屏布局**，无侧边栏，视觉上占据满屏：

```css
#profile-view.view.active {
  grid-template-columns: 1fr;  /* 单列布局 */
  padding: 0;
  width: 100%;
  max-width: 100%;
}
```

#### Hero 区域

- **头像展示**：大尺寸头像，带在线状态标识
- **基本信息**：姓名、职称、机构、位置
- **操作按钮**：右侧"发起合作"按钮，使用主深红色

#### 内容区域

- **快速信息卡片**：可用时间、研究方向标签
- **技术栈展示**：技术标签云
- **语言能力**：支持的语言列表
- **关于部分**：简短介绍和详细背景
- **成果展示**：教师角色显示论文/项目列表

#### 编辑功能

- **编辑按钮**：位于页面顶部导航栏右侧
- **编辑模态框**：大尺寸模态框，支持滚动
- **表单分组**：基本信息、研究方向、技术栈、语言、简介、成果等
- **实时保存**：编辑后立即更新显示

### 功能栏设计

#### 自动隐藏机制

顶部功能栏采用**智能隐藏**设计：

```css
.feature-bar {
  transform: translateY(-100%);  /* 默认隐藏 */
  transition: transform 0.3s ease;
}

.feature-bar:hover,
.feature-bar.show {
  transform: translateY(0);  /* 悬停时显示 */
}
```

- **默认状态**：功能栏隐藏在页面顶部外
- **触发显示**：鼠标移到页面顶部12px区域时自动显示
- **保持显示**：鼠标悬停在功能栏上时保持显示
- **平滑动画**：使用CSS过渡效果，体验流畅

#### 功能栏内容

- **当前角色显示**：显示用户当前角色（企业/教师/普通使用者/管理员）
- **功能按钮**：个人中心、出题、数据上传、审核题目（管理员）
- **退出登录**：右侧退出登录按钮

### 响应式设计

#### 断点系统

```css
/* 桌面端（默认） */
.view.active {
  grid-template-columns: 240px 1fr;
}

/* 平板端（900px以下） */
@media (max-width: 900px) {
  .view.active {
    grid-template-columns: 200px 1fr;
  }
}

/* 移动端（680px以下） */
@media (max-width: 680px) {
  .view.active {
    grid-template-columns: 1fr;  /* 单列布局 */
  }
  .sidebar {
    display: none;  /* 隐藏侧边栏 */
  }
}
```

#### 移动端优化

- **侧边栏折叠**：小屏幕下自动隐藏侧边栏
- **触摸友好**：按钮和交互元素增大点击区域
- **内容适配**：卡片和列表自动调整布局
- **字体缩放**：使用相对单位，支持系统字体缩放

### 交互细节

#### 按钮状态

- **默认状态**：浅灰边框，透明背景
- **悬停状态**：深红色文字，浅粉背景，柔和红边框
- **激活状态**：深红色文字，浅粉背景，主深红边框
- **禁用状态**：降低透明度，禁用指针事件

#### 卡片设计

- **背景**：纯白色（`#FFFFFF`）
- **边框**：浅灰色（`#E5E5E5`）
- **阴影**：轻微阴影（`0 2px 8px rgba(127, 0, 55, 0.08)`）
- **圆角**：8px-12px，现代感
- **悬停效果**：轻微提升阴影，增强层次感

#### 模态框设计

- **遮罩层**：半透明黑色背景（`rgba(0, 0, 0, 0.5)`）
- **内容区**：白色背景，圆角12px，居中显示
- **关闭按钮**：右上角×按钮，悬停时变红
- **动画效果**：淡入淡出，缩放动画

### 主题定制

平台支持明暗主题切换，可通过以下方式修改：

#### CSS 变量

在 `styles.css` 中修改 `:root` 和 `.theme-dark` 中的变量：

```css
:root {
  --red-dark: #7F0037;        /* 深红 */
  --red-primary: #A5192E;     /* 主深红 */
  --red-soft: #B8404A;        /* 柔和红 */
  --bg: #FAFAFA;              /* 主背景 */
  --bg-elev: #FFFFFF;         /* 卡片背景 */
  --text: #333333;            /* 主文字 */
  /* ... 更多变量 */
}

.theme-dark {
  --bg: #1A1A1A;             /* 深色背景 */
  --bg-elev: #2A2A2A;        /* 深色卡片 */
  --text: #E5E5E5;           /* 浅色文字 */
  /* ... 更多变量 */
}
```

#### 主题切换

- **切换按钮**：侧边栏品牌区域右上角
- **持久化**：主题选择保存到 localStorage
- **即时生效**：切换后立即应用，无需刷新

## 🔧 开发指南

### 添加新功能

1. **添加新视图**
   - 在 `index.html` 中添加新的 `<section class="view">`
   - 在 `app.js` 中添加视图切换逻辑

2. **添加新模块**
   - 使用 IIFE 模式封装模块
   - 通过 `window` 对象暴露接口
   - 监听自定义事件实现模块间通信

3. **扩展数据模型**
   - 在 `app.js` 中定义数据结构
   - 使用 localStorage 持久化
   - 触发 `projectsUpdated` 等事件通知更新

### 代码规范

- 使用 ES6+ 语法
- 函数和变量使用驼峰命名
- CSS 类名使用 BEM 命名规范
- 添加必要的注释和文档

## 📊 数据模型

### 项目对象（Project）

```javascript
{
  id: 'p1',                    // 唯一标识
  category: 'image',           // 分类
  subKey: 'cam-denoise',       // 子分类键
  title: '相机的图像去噪',      // 标题
  desc: '复杂背景下的高保真去噪', // 描述
  likes: 128,                   // 点赞数
  status: 'approved',          // 状态：pending/approved/rejected
  createdAt: '2024-01-01...',  // 创建时间
  createdBy: 'enterprise',      // 创建者角色
  createdByUsername: '企业用户' // 创建者用户名
}
```

### 待审核题目（Pending Problem）

```javascript
{
  id: 'p1234567890',
  category: 'image',
  subKey: 'new-denoise',
  title: '新题目',
  desc: '描述',
  background: '背景介绍',
  status: 'pending',
  likes: 0,
  createdAt: '2024-01-01...',
  createdBy: 'teacher',
  createdByUsername: '教师用户'
}
```

### 笔记本单元格（Notebook Cell）

```javascript
{
  id: 'cell-0',
  type: 'code' | 'markdown' | 'table',
  content: '代码或文本内容',
  language: 'python',
  output: '执行结果'
}
```

## 🐛 已知问题

- [ ] 代码执行环境为模拟实现，实际项目中需要后端支持
- [ ] 文件上传功能尚未实现
- [ ] 审核历史记录未保存
- [ ] 移动端适配需要进一步优化

## 🔮 未来计划

- [x] ~~代码智能体集成（Aider AI）~~ ✅ 已完成
- [ ] 后端 API 集成
- [ ] 真实的代码执行环境
- [ ] 用户认证系统
- [ ] 数据可视化
- [ ] 协作功能
- [ ] 导出功能（PDF、Markdown）
- [ ] 搜索功能
- [ ] 通知系统
- [ ] 代码版本控制
- [ ] 代码审查功能

## 📝 更新日志

### v1.1.0 (2025-11-15) 🎉 新版本
- ✨ **重大更新**: 集成 Aider AI 代码智能体
- ✨ 添加代码生成、编辑、解释功能
- ✨ 支持多种编程语言
- ✨ 完善的后端 API 服务
- ✨ 优雅的降级方案（无后端也可使用）
- 📖 新增完整的文档体系
- 🔧 添加启动脚本和配置工具

### v1.0.0 (2024-01-XX)
- ✨ 初始版本发布
- ✨ 交互式笔记本功能
- ✨ 项目管理系统
- ✨ 出题和审核功能
- ✨ AI Agent 集成
- ✨ 用户角色系统

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request


---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 👥 作者

- **zhaoziwei** - 初始开发

## 🙏 致谢

- 感谢所有贡献者的支持
- 参考了 Jupyter Notebook 的交互设计
- 使用了 Inter 字体

## 📚 相关文档

- 📖 [快速开始指南](QUICK_START.md) - 5 分钟快速上手
- 🔧 [Aider AI 技术文档](AIDER_README.md) - 详细的技术说明
- 📘 [使用指南](USAGE_GUIDE.md) - 完整的功能使用说明
- ✅ [测试文档](TEST_GUIDE.md) - 测试步骤和验证
- 📝 [实现总结](IMPLEMENTATION_SUMMARY.md) - 开发实现细节

## 🌟 特别说明

### 代码智能体功能

本项目集成了 [Aider AI](https://github.com/Aider-AI/aider)，这是一个强大的 AI 编程助手。主要特性：

- ✅ **智能代码生成**: 根据自然语言描述生成代码
- ✅ **代码编辑优化**: 修改和优化现有代码
- ✅ **代码解释分析**: 详细解释代码工作原理
- ✅ **多语言支持**: Python, JavaScript, Java, C, C++, Go, Rust 等
- ✅ **文件管理**: 自动生成项目结构和配置文件
- ✅ **优雅降级**: 无后端也能体验基本功能

### 使用要求

- **前端功能**: 无需任何配置，直接打开即用
- **完整功能**: 需要 OpenAI API Key 或其他支持的 LLM API

## 📧 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 Issue
- 查看文档
- 发送邮件

---

**⭐ 如果这个项目对您有帮助，请给个 Star！**

**🎉 现在就试试代码智能体功能吧！**

