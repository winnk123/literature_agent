# AI 科创平台 - 项目文档

## 📋 项目概述

AI 科创平台是一个面向 AI 研究者和学习者的在线教育平台，提供项目展示、学习、实验和协作功能。平台采用单页应用（SPA）架构，使用原生 JavaScript 实现，无需框架依赖。

## 📁 文件结构

```
AI-/
├── index.html      # HTML 结构文件
├── app.js          # JavaScript 核心逻辑（~2917行）
├── styles.css      # CSS 样式文件（~810行）
└── README.md       # 项目文档（本文件）
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
    - 主导航菜单 (`nav.sidebar__nav`):
      - 首页 (`#homeNavBtn`)
      - 项目 (`#projectsNavBtn`) - 带分类子菜单 (`#categoryList`)
      - 我要出题 (`#createNavBtn`)
    - 个人中心 (`div.sidebar__profile`)
  - **主内容区** (`main.content`):
    - Hero 区域 (`#homeHero`) - 包含标题和登录/注册按钮
    - 项目展示区 (`#projectsView`) - 项目卡片网格 (`#projectsGrid`)

##### 1.2.2 详情页视图 (`#detail-view`)
- **布局**: 1:4:4 比例（侧边栏:中间内容:右侧面板）
- **组件**:
  - **左侧边栏**:
    - 品牌标识和主题切换 (`#themeToggle2`)
    - 返回按钮 (`#backBtnSide`)
    - 详情页导航菜单 (`#detailMenu`)
    - 代码语言选择器 (`language-selector`)
    - 个人中心
  - **中间内容区** (`section.detail__middle`):
    - 面包屑导航 (`detail__breadcrumbs`)
    - 详情菜单 (`detail__menu`)
    - 视频演示区 (`detail__video`)
    - 文章内容 (`article.detail__content`):
      - 标题 (`#projectTitle`)
      - 元信息 (`article__meta`)
      - 内容区域 (`#detailContent`)
  - **右侧面板** (`aside.detail__qa`):
    - QA 欢迎页 (`#qaWelcome`) - 初始显示
    - QA 聊天界面 (`#qaChat`) - 包含文献/科研标签页
    - 文件查看按钮 (`#qaFilesBtn`)

##### 1.2.3 出题页面视图 (`#create-view`) - **待开发**
- **状态**: 当前 HTML 中未定义，需要新增
- **计划布局**: 独立页面，包含出题表单和相关功能

#### 1.3 模态框（Modals）

##### 1.3.1 登录模态框 (`#loginModal`)
- **结构**: 模态框 + 遮罩层
- **内容**: 角色选择卡片
  - 企业 (`data-role="enterprise"`)
  - 高校教师 (`data-role="teacher"`)
  - 普通使用者 (`data-role="user"`)
- **关闭按钮**: `#closeLoginModal`

##### 1.3.2 注册模态框 (`#registerModal`)
- **结构**: 表单模态框
- **表单字段** (`#registerForm`):
  - 用户名
  - 邮箱
  - 密码
  - 确认密码
  - 角色选择
- **关闭按钮**: `#closeRegisterModal`
- **切换登录**: `#switchToLogin`

##### 1.3.3 文件查看模态框 (`#filesModal`)
- **用途**: 显示 AI Agent 生成的文件列表
- **内容**: 文件列表容器 (`#filesList`)
- **关闭按钮**: `#closeFilesModal`

#### 1.4 其他组件

##### 1.4.1 功能栏 (`#featureBar`)
- **显示条件**: 登录后显示
- **内容**:
  - 当前角色显示 (`#currentRole`)
  - 功能按钮:
    - 出题 (`#createProblemBtn`)
    - 数据上传 (`#uploadDataBtn`)
    - 退出登录 (`#logoutBtn`)

##### 1.4.2 划词工具栏 (`#textToolbar`)
- **功能**: 文本选择后的操作工具栏
- **按钮**:
  - 询问AI (`#askAI`)
  - 高亮 (`#highlightText`) - 带颜色选择 (`#highlightColors`)
  - 下划线 (`#underlineText`)
  - 删除线 (`#strikeText`)

---

### 2. `app.js` - JavaScript 核心逻辑

#### 2.1 代码结构概览

```javascript
(function () {
  // IIFE 包装，避免全局污染
  
  // 1. DOM 查询工具函数
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
  // 15. 初始化代码
})();
```

#### 2.2 核心模块详解

##### 2.2.1 DOM 工具函数（第1-3行）
```javascript
const qs = (s, r = document) => r.querySelector(s);      // 单个元素查询
const qsa = (s, r = document) => Array.from(r.querySelectorAll(s));  // 多个元素查询
```

##### 2.2.2 DOM 元素选择器（第5-28行）
- **视图元素**: `homeView`, `detailView`
- **模态框**: `loginModal`, `registerModal`
- **按钮**: `loginBtn`, `registerBtn`, `createProblemBtn`, `uploadDataBtn`, `logoutBtn`
- **导航**: `homeNavBtn`, `projectsNavBtn`, `createNavBtn`
- **内容区**: `homeHero`, `projectsView`, `projectsGrid`, `categoryListEl`

##### 2.2.3 全局状态变量（第30行）
```javascript
let currentUserRole = null;  // 当前用户角色
```

##### 2.2.4 主题切换模块（第32-36行）
- **功能**: 切换明暗主题
- **实现**: 切换 `theme-dark` / `theme-light` 类名
- **按钮**: `#themeToggle`, `#themeToggle2`

##### 2.2.5 动画效果模块（第38-511行）

###### 密集粒子云 (`createDenseParticleCloud`, 第39-305行)
- **功能**: 创建文字粒子云动画
- **文字**: "有你想学习的任何东西"
- **粒子数**: 1200个
- **效果**: 粒子从随机位置飞向文字位置

###### 科技粒子 (`createTechParticles`, 第307-410行)
- **功能**: 背景科技感粒子效果
- **粒子类型**: 小点、线条、光晕

###### 文字发光 (`addTextGlow`, 第411-438行)
- **功能**: 为标题文字添加发光动画效果

###### 扇形展开动画 (`initFanSpreadAnimation`, 第439-503行)
- **功能**: Hero 标题文字的扇形展开动画
- **目标元素**: `#learnEveryHere`

###### 动画初始化 (`initAnimations`, 第500-511行)
- **功能**: 统一初始化所有动画效果
- **触发时机**: 首页显示时

##### 2.2.6 视图管理模块（第513-730行）

###### 视图切换 (`switchView`, 第2095-2101行)
```javascript
function switchView(view) {
  // 隐藏所有视图
  // 显示目标视图 ('home' | 'detail' | 'create')
}
```

###### 首页视图 (`showHomeView`, 第634-643行)
- **功能**: 显示首页，重置状态
- **操作**:
  - 设置导航激活状态
  - 显示 Hero 区域
  - 隐藏项目视图
  - 清空项目网格
  - 初始化扇形动画

###### 项目视图 (`showProjectsView`, 第645-665行)
- **功能**: 显示项目列表
- **操作**:
  - 隐藏 Hero 区域
  - 显示项目视图
  - 渲染项目卡片

###### 分类管理
- `toggleCategoryList` (第668-678行): 切换分类列表显示/隐藏
- `renderCategories` (第681-702行): 渲染分类列表
- `toggleCategory` (第704-730行): 切换分类展开/收起

##### 2.2.7 项目数据和管理（第550-730行）

###### 数据结构
```javascript
const categories = [  // 分类数据
  { key: 'image', name: '图像', items: [...] },
  { key: 'audio', name: '语音', items: [...] },
  { key: 'llm', name: 'LLM', items: [...] },
  { key: 'mllm', name: 'MLLM', items: [...] },
  { key: 'agent', name: 'Agent', items: [...] }
];

const projects = [  // 项目数据
  { id: 'p1', category: 'image', subKey: 'cam-denoise', title: '...', desc: '...', likes: 128 },
  // ...
];
```

###### 项目卡片渲染 (`renderCards`, 第584-627行)
- **功能**: 将项目数据渲染为卡片网格
- **事件**: 点击卡片打开详情页

###### 项目详情 (`openDetail`, 第732-752行)
- **功能**: 打开项目详情页
- **操作**:
  - 构建详情菜单
  - 设置面包屑
  - 渲染默认章节
  - 切换视图
  - 更新 URL hash
  - 重置 QA Agent

##### 2.2.8 Notebook 功能模块（第804-1330行）

###### 核心数据结构
```javascript
let notebookCells = [];  // Notebook 单元格数组
let cellCounter = 0;      // 单元格计数器
const pythonEnv = {      // Python 执行环境
  variables: {},
  functions: {}
};
```

###### 主要函数
- `createNotebookCell` (第843-854行): 创建单元格对象
- `renderNotebookCell` (第856-1067行): 渲染单元格到 DOM
- `renderNotebook` (第1268-1330行): 渲染整个 Notebook
- `runCell` (第1163-1267行): 执行单元格代码
- `renderMarkdown` (第809-841行): Markdown 渲染器

###### 单元格类型
- **代码单元格** (`code`): 可编辑、可执行的代码块
- **Markdown 单元格** (`markdown`): 可编辑的 Markdown 文本
- **表格单元格** (`table`): 可视化数据表格

###### 单元格操作
- `moveCellUp` / `moveCellDown`: 移动单元格
- `addCellAbove` / `addCellBelow`: 添加单元格
- `deleteCell`: 删除单元格
- `enterMarkdownEditMode` / `exitMarkdownEditMode`: Markdown 编辑模式

##### 2.2.9 详情页渲染模块（第1331-1858行）

###### 详情章节渲染 (`renderDetailSection`, 第1331-1691行)
- **支持的章节**:
  - `background`: 背景介绍
  - `model`: 模型介绍
  - `model-intro`: 模型详细介绍
  - `baseline`: Baseline 对比
  - `idea`: IDEA 引导
  - `personalize`: 个性化检验（10道选择题）
  - `comments`: 留言区

###### 个性化检验 (`renderPersonalizeSection`, 第1693-1858行)
- **功能**: 渲染10道选择题的测验
- **数据结构**: `quizData` 数组
- **交互**: 选择答案、提交、显示结果

###### 留言区 (`renderCommentsSection`, 第1859-2094行)
- **功能**: 渲染留言列表和发表留言表单
- **数据存储**: localStorage

##### 2.2.10 登录/注册模块（第2155-2431行）

###### 登录功能 (`handleLogin`, 第2370-2431行)
- **角色**: enterprise, teacher, user
- **操作**:
  - 设置 `currentUserRole`
  - 显示功能栏
  - 更新角色显示
  - 关闭登录模态框

###### 注册功能 (`registerUser`, 第2262-2289行)
- **功能**: 用户注册（当前为模拟实现）
- **字段**: 用户名、邮箱、密码、角色

###### 登录表单 (`showLoginForm`, 第2302-2369行)
- **功能**: 显示登录表单界面

##### 2.2.11 QA Agent 模块（第2454-2641行）

###### 核心变量
```javascript
const qaTabs = qsa('.qa__tab');           // 标签页（文献/科研）
const qaMessages = qs('#qaMessages');     // 消息容器
const qaInput = qs('#qaInput');           // 输入框
const qaSendBtn = qs('#qaSendBtn');       // 发送按钮
const qaFilesBtn = qs('#qaFilesBtn');     // 文件按钮
let hasGeneratedFiles = false;            // 是否已生成文件
```

###### 主要函数
- `switchToChat` (第2542-2556行): 切换到聊天界面
- `sendQaMessage` (第2581-2618行): 发送消息并模拟 AI 回复

###### 生成文件列表 (`generatedFiles`, 第2462-2541行)
- **文件类型**: Python 代码、配置文件、README
- **显示**: 通过文件模态框展示

##### 2.2.12 文件管理模块（第2644-2725行）

###### 文件列表渲染 (`renderFilesList`, 第2671-2725行)
- **功能**: 渲染生成的文件列表
- **操作**: 预览、下载文件

##### 2.2.13 划词工具栏模块（第2726-2907行）

###### 核心变量
```javascript
let selectedText = '';      // 选中的文本
let selectedRange = null;    // 选中的范围
```

###### 主要功能
- `applyHighlight`: 应用高亮
- `applyUnderline`: 应用下划线
- `applyStrikethrough`: 应用删除线
- `saveAnnotations` / `loadAnnotations`: 保存/加载标注

##### 2.2.14 路由管理（第2432-2453行）

###### 浏览器历史管理
- **返回按钮** (`#backBtnSide`): 返回首页
- **popstate 事件**: 处理浏览器前进/后退

##### 2.2.15 初始化代码（第513-548行）
- **页面加载**: 初始化动画和视图
- **导航绑定**: 绑定侧边栏导航按钮事件

---

### 3. `styles.css` - CSS 样式文件

#### 3.1 CSS 变量系统（第1-24行）

###### 明暗主题变量
```css
:root {
  --brand: #A0522D;        /* 品牌色（温暖褐红色）*/
  --bg: #F5F1EA;          /* 背景色（米色）*/
  --text: #3E2723;        /* 文字色（深褐色）*/
  /* ... */
}

.theme-dark {
  --bg: #0f1115;          /* 深色背景 */
  --text: #e9edf4;        /* 浅色文字 */
  /* ... */
}
```

#### 3.2 布局系统

###### 视图布局（第48-63行）
```css
.view { display: none; }
.view.active { display: grid; }
#home-view.view.active { grid-template-columns: 240px 1fr; }
#detail-view.view.active { grid-template-columns: 240px 1fr 1fr; }
```

###### 侧边栏布局（第58-72行）
- **首页侧边栏**: `grid-template-rows: auto 1fr auto auto`
- **详情页侧边栏**: `grid-template-rows: auto auto 1fr auto`

#### 3.3 组件样式

###### 导航菜单（第81-98行）
- `.nav__item`: 导航项样式
- `.nav__item.is-active`: 激活状态
- `.nav__sublist`: 子菜单列表

###### 卡片样式（第200-250行，估算）
- `.card`: 项目卡片容器
- `.card__poster`: 卡片海报区
- `.card__body`: 卡片内容区

###### 模态框样式（第300-400行，估算）
- `.modal`: 模态框容器
- `.modal__overlay`: 遮罩层
- `.modal__content`: 模态框内容

###### Notebook 样式（第500-700行，估算）
- `.notebook-cell`: 单元格容器
- `.code-cell`: 代码单元格
- `.markdown-cell`: Markdown 单元格
- `.table-cell`: 表格单元格

###### QA Agent 样式（第439-455行）
- `.qa__welcome`: 欢迎页面
- `.qa__chat`: 聊天界面
- `.msg`: 消息样式
- `.msg--ai` / `.msg--user`: AI/用户消息

#### 3.4 响应式设计（第448-565行）

###### 媒体查询
```css
@media (max-width: 900px) { /* 平板 */ }
@media (max-width: 680px) { /* 手机 */ }
```

---

## 🎯 "我要出题" 功能开发指南

### 设计原则

1. **模块独立性**: 出题功能应作为独立模块，不干扰其他功能
2. **数据接口**: 通过标准化的数据接口与其他模块交互
3. **视图隔离**: 使用独立的视图页面，不修改现有视图结构
4. **样式隔离**: 使用独立 CSS 类名前缀，避免样式冲突

### 推荐的文件结构

```
AI-/
├── index.html              # 添加 #create-view 视图
├── app.js                  # 添加 ProblemCreation 模块
├── styles.css             # 添加 .problem-creation-* 样式
└── modules/                # 可选：未来可拆分为模块文件
    └── problem-creation.js # 出题功能独立模块（未来）
```

### 模块设计建议

#### 1. HTML 结构（在 `index.html` 中添加）

```html
<!-- 出题页面视图 -->
<section id="create-view" class="view">
  <aside class="sidebar">
    <!-- 侧边栏：品牌、导航、返回按钮 -->
  </aside>
  <main class="content problem-creation-content">
    <div class="problem-creation-container">
      <header class="problem-creation-header">
        <h1>我要出题</h1>
        <button id="closeCreateViewBtn">× 关闭</button>
      </header>
      <form id="createProblemForm" class="problem-creation-form">
        <!-- 表单字段 -->
      </form>
    </div>
  </main>
</section>
```

#### 2. JavaScript 模块结构（在 `app.js` 中添加）

```javascript
// ============================================
// 出题功能模块 - Problem Creation Module
// ============================================
// 作者: zhaoziwei
// 说明: 独立的出题功能模块，通过数据接口与其他模块交互

(function ProblemCreationModule() {
  'use strict';  // 严格模式，避免变量污染
  
  // ========== 模块私有变量 ==========
  const MODULE_NAME = 'ProblemCreation';
  const STORAGE_KEY_PENDING = 'ai_platform_pending_problems';
  const STORAGE_KEY_PROJECTS = 'ai_platform_projects';
  
  // DOM 元素（仅在模块内使用）
  const createView = qs('#create-view');
  const createProblemForm = qs('#createProblemForm');
  const backFromCreateBtn = qs('#backFromCreateBtn');
  const closeCreateViewBtn = qs('#closeCreateViewBtn');
  
  // ========== 数据接口 ==========
  // 这些函数是模块对外暴露的唯一接口
  
  /**
   * 获取待审核题目列表
   * @returns {Array} 待审核题目数组
   */
  function getPendingProblems() {
    try {
      const data = localStorage.getItem(STORAGE_KEY_PENDING);
      return data ? JSON.parse(data) : [];
    } catch (e) {
      console.error('[ProblemCreation] 读取待审核题目失败:', e);
      return [];
    }
  }
  
  /**
   * 保存待审核题目列表
   * @param {Array} problems - 题目数组
   */
  function savePendingProblems(problems) {
    try {
      localStorage.setItem(STORAGE_KEY_PENDING, JSON.stringify(problems));
      // 触发自定义事件，通知其他模块数据已更新
      window.dispatchEvent(new CustomEvent('pendingProblemsUpdated', {
        detail: { problems }
      }));
    } catch (e) {
      console.error('[ProblemCreation] 保存待审核题目失败:', e);
    }
  }
  
  /**
   * 获取已发布项目列表
   * @returns {Array} 项目数组
   */
  function getPublishedProjects() {
    try {
      const data = localStorage.getItem(STORAGE_KEY_PROJECTS);
      return data ? JSON.parse(data) : [];
    } catch (e) {
      console.error('[ProblemCreation] 读取项目列表失败:', e);
      return [];
    }
  }
  
  /**
   * 添加新项目到已发布列表（由审核模块调用）
   * @param {Object} project - 项目对象
   */
  function addPublishedProject(project) {
    try {
      const projects = getPublishedProjects();
      projects.push(project);
      localStorage.setItem(STORAGE_KEY_PROJECTS, JSON.stringify(projects));
      // 触发自定义事件，通知其他模块数据已更新
      window.dispatchEvent(new CustomEvent('projectsUpdated', {
        detail: { projects }
      }));
    } catch (e) {
      console.error('[ProblemCreation] 添加项目失败:', e);
    }
  }
  
  // ========== 模块内部函数 ==========
  
  /**
   * 初始化出题表单
   */
  function initForm() {
    if (!createProblemForm) return;
    
    createProblemForm.addEventListener('submit', handleFormSubmit);
    
    // 表单验证
    const requiredFields = createProblemForm.querySelectorAll('[required]');
    requiredFields.forEach(field => {
      field.addEventListener('blur', validateField);
    });
  }
  
  /**
   * 处理表单提交
   */
  function handleFormSubmit(e) {
    e.preventDefault();
    
    // 收集表单数据
    const formData = collectFormData();
    
    // 验证数据
    if (!validateFormData(formData)) {
      return;
    }
    
    // 创建题目对象
    const problem = createProblemObject(formData);
    
    // 保存到待审核列表
    const pendingList = getPendingProblems();
    pendingList.push(problem);
    savePendingProblems(pendingList);
    
    // 显示成功提示
    showSuccessMessage('题目已提交，等待管理员审核！');
    
    // 重置表单
    createProblemForm.reset();
    
    // 返回首页
    navigateToHome();
  }
  
  /**
   * 收集表单数据
   */
  function collectFormData() {
    return {
      title: qs('#problemTitle', createProblemForm)?.value.trim() || '',
      category: qs('#problemCategory', createProblemForm)?.value || '',
      subKey: qs('#problemSubKey', createProblemForm)?.value.trim() || '',
      desc: qs('#problemDesc', createProblemForm)?.value.trim() || '',
      background: qs('#problemBackground', createProblemForm)?.value.trim() || ''
    };
  }
  
  /**
   * 验证表单数据
   */
  function validateFormData(data) {
    if (!data.title || !data.category || !data.subKey || !data.desc) {
      showErrorMessage('请填写所有必填字段！');
      return false;
    }
    return true;
  }
  
  /**
   * 创建题目对象
   */
  function createProblemObject(formData) {
    return {
      id: 'p' + Date.now(),
      title: formData.title,
      category: formData.category,
      subKey: formData.subKey,
      desc: formData.desc,
      background: formData.background || '',
      likes: 0,
      status: 'pending',
      createdAt: new Date().toISOString(),
      createdBy: getCurrentUserRole()  // 从全局状态获取
    };
  }
  
  /**
   * 获取当前用户角色（从全局状态）
   */
  function getCurrentUserRole() {
    // 注意：这里访问全局变量 currentUserRole
    // 这是模块间数据交互的唯一方式
    return window.currentUserRole || 'user';
  }
  
  /**
   * 导航到首页
   */
  function navigateToHome() {
    // 调用全局的视图切换函数
    if (typeof window.switchView === 'function') {
      window.switchView('home');
    }
    // 更新 URL
    if (window.history) {
      window.history.pushState({ view: 'home' }, '', '#');
    }
  }
  
  /**
   * 显示成功消息
   */
  function showSuccessMessage(message) {
    alert(message);  // 可替换为更优雅的提示组件
  }
  
  /**
   * 显示错误消息
   */
  function showErrorMessage(message) {
    alert(message);  // 可替换为更优雅的提示组件
  }
  
  /**
   * 初始化返回按钮
   */
  function initNavigationButtons() {
    if (backFromCreateBtn) {
      backFromCreateBtn.addEventListener('click', navigateToHome);
    }
    if (closeCreateViewBtn) {
      closeCreateViewBtn.addEventListener('click', navigateToHome);
    }
  }
  
  // ========== 模块初始化 ==========
  
  /**
   * 初始化模块
   */
  function init() {
    if (!createView) {
      console.warn('[ProblemCreation] 出题视图未找到，模块未初始化');
      return;
    }
    
    initForm();
    initNavigationButtons();
    
    console.log(`[${MODULE_NAME}] 模块初始化完成`);
  }
  
  // ========== 模块导出 ==========
  // 将需要对外暴露的函数挂载到全局对象
  
  window.ProblemCreation = {
    getPendingProblems,
    savePendingProblems,
    getPublishedProjects,
    addPublishedProject,
    init
  };
  
  // 自动初始化
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
  
})();
```

#### 3. CSS 样式结构（在 `styles.css` 中添加）

```css
/* ============================================
   出题功能样式 - Problem Creation Styles
   ============================================
   作者: zhaoziwei
   说明: 独立的样式模块，使用 .problem-creation-* 前缀
   ============================================ */

/* 出题视图布局 */
#create-view.view.active {
  grid-template-columns: 240px 1fr;
  column-gap: 24px;
  padding: 0 24px;
}

/* 出题内容容器 */
.problem-creation-content {
  padding: 24px 0;
}

.problem-creation-container {
  max-width: 900px;
  margin: 0 auto;
}

/* 出题头部 */
.problem-creation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.problem-creation-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: var(--text);
}

/* 出题表单 */
.problem-creation-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.problem-creation-form .form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.problem-creation-form .form-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}

.problem-creation-form .form-label .required {
  color: #e74c3c;
}

.problem-creation-form .input,
.problem-creation-form textarea {
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-elev);
  color: var(--text);
  font-size: 14px;
  font-family: inherit;
}

.problem-creation-form textarea {
  resize: vertical;
  min-height: 120px;
}

.problem-creation-form .form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 8px;
}

/* 响应式 */
@media (max-width: 680px) {
  #create-view.view.active {
    grid-template-columns: 1fr;
    padding: 0 16px;
  }
  
  .problem-creation-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
}
```

### 数据接口规范

#### 题目对象结构
```javascript
{
  id: string,              // 唯一标识符，格式: 'p' + timestamp
  title: string,            // 题目名称（必填）
  category: string,        // 分类（必填）: 'image' | 'audio' | 'llm' | 'mllm' | 'agent'
  subKey: string,          // 子分类（必填）
  desc: string,            // 项目描述（必填）
  background: string,      // 背景介绍（可选）
  likes: number,          // 点赞数，默认 0
  status: string,         // 状态: 'pending' | 'approved' | 'rejected'
  createdAt: string,      // 创建时间，ISO 格式
  createdBy: string       // 创建者角色: 'enterprise' | 'teacher' | 'user'
}
```

#### 数据存储键名
- **待审核题目**: `ai_platform_pending_problems`
- **已发布项目**: `ai_platform_projects`

#### 自定义事件
- **`pendingProblemsUpdated`**: 待审核题目列表更新时触发
  ```javascript
  window.addEventListener('pendingProblemsUpdated', (e) => {
    const { problems } = e.detail;
    // 更新审核模块的显示
  });
  ```

- **`projectsUpdated`**: 项目列表更新时触发
  ```javascript
  window.addEventListener('projectsUpdated', (e) => {
    const { projects } = e.detail;
    // 更新项目展示模块的显示
  });
  ```

### 与其他模块的交互

#### 1. 与视图管理模块的交互
```javascript
// 打开出题页面
if (typeof window.switchView === 'function') {
  window.switchView('create');
}

// 返回首页
if (typeof window.switchView === 'function') {
  window.switchView('home');
}
```

#### 2. 与用户认证模块的交互
```javascript
// 获取当前用户角色
const role = window.currentUserRole || 'user';

// 检查权限
if (role === 'enterprise' || role === 'teacher') {
  // 允许出题
}
```

#### 3. 与项目展示模块的交互
```javascript
// 监听项目更新事件
window.addEventListener('projectsUpdated', (e) => {
  const { projects } = e.detail;
  // 重新渲染项目列表
  if (typeof window.renderCards === 'function') {
    window.renderCards(projects);
  }
});
```

### 开发检查清单

- [ ] HTML: 添加 `#create-view` 视图结构
- [ ] HTML: 添加出题表单字段
- [ ] JavaScript: 创建 `ProblemCreationModule` 模块
- [ ] JavaScript: 实现数据接口函数
- [ ] JavaScript: 实现表单提交逻辑
- [ ] JavaScript: 实现导航逻辑
- [ ] CSS: 添加 `.problem-creation-*` 样式
- [ ] CSS: 实现响应式布局
- [ ] 测试: 表单验证
- [ ] 测试: 数据保存和读取
- [ ] 测试: 与其他模块的交互
- [ ] 测试: 权限控制

### 注意事项

1. **不要修改现有代码**: 除非必要，不要修改队友已经写好的代码
2. **使用命名空间**: 所有函数和变量使用 `problem-creation-` 或 `ProblemCreation` 前缀
3. **数据隔离**: 使用独立的 localStorage 键名
4. **事件通信**: 使用自定义事件进行模块间通信，而不是直接调用函数
5. **错误处理**: 所有数据操作都要有 try-catch 错误处理
6. **代码注释**: 重要函数都要有 JSDoc 注释

---

## 🔧 开发环境

### 本地运行
```bash
# 启动本地服务器
python3 -m http.server 8000

# 访问
http://localhost:8000
```

### 浏览器支持
- Chrome/Edge (推荐)
- Firefox
- Safari

---

## 📝 更新日志

### 2024-XX-XX
- 初始项目文档
- 完成代码结构分析
- 设计"我要出题"功能模块架构

---

## 👥 贡献者

- **wangmingxuan**: 项目主框架、详情页、QA Agent、Notebook 等功能
- **zhaoziwei**: "我要出题"功能模块、管理员审核模块

---

## 📝 更新日志

### v1.0.0 (2024-01-XX)
- ✨ 初始版本发布
- ✨ 交互式笔记本功能
- ✨ 项目管理系统
- ✨ 出题和审核功能
- ✨ AI Agent 集成
- ✨ 用户角色系统

## 🐛 已知问题

- [ ] 代码执行环境为模拟实现，实际项目中需要后端支持
- [ ] 文件上传功能尚未实现
- [ ] 审核历史记录未保存
- [ ] 移动端适配需要进一步优化

## 🔮 未来计划

- [ ] 后端 API 集成
- [ ] 真实的代码执行环境
- [ ] 用户认证系统
- [ ] 数据可视化
- [ ] 协作功能
- [ ] 导出功能（PDF、Markdown）
- [ ] 搜索功能
- [ ] 通知系统

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- 感谢所有贡献者的支持
- 参考了 Jupyter Notebook 的交互设计
- 使用了 Inter 字体

## 📧 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 Issue
- 发送邮件

---

**⭐ 如果这个项目对您有帮助，请给个 Star！**
