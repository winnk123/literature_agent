# 🎨 UI 修改指南

> 本指南帮助您快速定位和修改界面设计元素，实现 UI 包的快速切换，同时不影响功能。

---

## 📋 目录

1. [UI 组件位置映射](#ui-组件位置映射)
2. [快速切换 UI 包](#快速切换-ui-包)
3. [按钮圆角修改](#按钮圆角修改)
4. [Emoji 替换指南](#emoji-替换指南)
5. [Logo 和图标系统](#logo-和图标系统)
6. [颜色系统](#颜色系统)
7. [字体和排版](#字体和排版)
8. [最佳实践](#最佳实践)

---

## UI 组件位置映射

### 核心文件结构

```
项目根目录/
├── index.html          # HTML 结构（UI 元素定义）
├── styles.css          # 样式文件（所有 UI 样式）
└── app.js              # 功能逻辑（不涉及 UI 样式）
```

### 主要 UI 组件位置

| 组件类型 | 文件位置 | 行数范围 | 说明 |
|---------|---------|---------|------|
| **颜色变量** | `styles.css` | 1-24 | CSS 变量定义 |
| **按钮样式** | `styles.css` | 376-397 | `.btn`, `.btn--primary`, `.btn--secondary`, `.btn--ghost` |
| **卡片样式** | `styles.css` | 408-416 | `.card`, `.card__poster`, `.card__body` |
| **Logo** | `index.html` | 20, 105, 277 | `.brand__logo`, `.ai-logo` |
| **导航图标** | `index.html` | 31-52 | SVG 图标（导航菜单） |
| **Emoji 图标** | `index.html` | 157, 161, 396-411, 547-557 | 各种 emoji 使用 |
| **表单输入** | `styles.css` | 373-374 | `.input` 样式 |
| **模态框** | `styles.css` | 886-909 | `.modal` 相关样式 |

---

## 快速切换 UI 包

### 方法一：创建 UI 主题文件（推荐）

#### 1. 创建新的 UI 主题文件

创建 `styles-ui-hard.css`（硬朗风格）：

```css
/* styles-ui-hard.css - 硬朗风格 UI 包 */

/* 覆盖圆角设置 */
:root {
  --ui-border-radius-sm: 2px;   /* 小圆角 */
  --ui-border-radius-md: 4px;   /* 中等圆角 */
  --ui-border-radius-lg: 6px;   /* 大圆角 */
  --ui-border-radius-xl: 8px;   /* 超大圆角 */
  --ui-border-radius-full: 0;   /* 完全无圆角 */
}

/* 按钮圆角覆盖 */
.btn { border-radius: var(--ui-border-radius-md) !important; }
.btn--primary { border-radius: var(--ui-border-radius-md) !important; }
.btn--secondary { border-radius: var(--ui-border-radius-md) !important; }
.btn--ghost { border-radius: var(--ui-border-radius-sm) !important; }
.btn--large { border-radius: var(--ui-border-radius-lg) !important; }

/* 卡片圆角覆盖 */
.card { border-radius: var(--ui-border-radius-lg) !important; }
.card__poster { border-radius: 0 !important; }

/* 输入框圆角覆盖 */
.input { border-radius: var(--ui-border-radius-md) !important; }
.search__wrapper { border-radius: var(--ui-border-radius-md) !important; }

/* 其他组件圆角覆盖 */
.badge { border-radius: var(--ui-border-radius-sm) !important; }
.chip { border-radius: var(--ui-border-radius-sm) !important; }
.modal__content { border-radius: var(--ui-border-radius-lg) !important; }
```

#### 2. 在 `index.html` 中引入

在 `index.html` 的 `<head>` 部分添加：

```html
<!-- 默认 UI（圆角风格） -->
<link rel="stylesheet" href="styles.css" />

<!-- 硬朗风格 UI（取消注释以启用） -->
<!-- <link rel="stylesheet" href="styles-ui-hard.css" /> -->
```

#### 3. 切换 UI 包

只需注释/取消注释对应的 CSS 文件即可：

```html
<!-- 切换到硬朗风格 -->
<link rel="stylesheet" href="styles.css" />
<link rel="stylesheet" href="styles-ui-hard.css" />
```

### 方法二：使用 CSS 变量覆盖

在 `styles.css` 开头添加 UI 主题变量：

```css
:root {
  /* 原有颜色变量 */
  --brand: #A0522D;
  /* ... */
  
  /* 新增：UI 风格变量 */
  --ui-style: 'rounded';  /* 'rounded' 或 'hard' */
  --ui-border-radius-base: 10px;  /* 基础圆角 */
}

/* 硬朗风格覆盖 */
[data-ui-style="hard"] {
  --ui-border-radius-base: 4px;
}

/* 应用圆角变量 */
.btn { border-radius: var(--ui-border-radius-base); }
```

在 `index.html` 的 `<body>` 标签添加属性：

```html
<body class="theme-light" data-ui-style="hard">
```

---

## 按钮圆角修改

### 当前圆角设置统计

- **总圆角使用次数**：131 处
- **主要组件圆角值**：
  - 按钮：`10px`, `8px`, `14px`
  - 卡片：`12px`
  - 输入框：`10px`, `999px`（完全圆形）
  - 徽章：`999px`（完全圆形）

### 快速修改所有按钮圆角

#### 位置：`styles.css`

**主要按钮样式位置**：

```css
/* 第 376 行：基础按钮 */
.btn { 
  border-radius: 10px;  /* ← 修改这里 */
}

/* 第 377 行：主要按钮 */
.btn--primary { 
  border-radius: 10px;  /* ← 修改这里 */
}

/* 第 278 行：大按钮 */
.btn--large { 
  border-radius: 14px;  /* ← 修改这里 */
}

/* 第 388 行：幽灵按钮 */
.btn--ghost { 
  border-radius: 8px;  /* ← 修改这里 */
}

/* 第 369 行：搜索按钮 */
.search__btn { 
  border-radius: 999px;  /* ← 修改这里（完全圆形） */
}
```

#### 批量替换脚本

使用以下命令批量替换（在项目根目录执行）：

```bash
# 将所有按钮圆角改为 4px（硬朗风格）
sed -i '' 's/border-radius: 10px/border-radius: 4px/g' styles.css
sed -i '' 's/border-radius: 8px/border-radius: 4px/g' styles.css
sed -i '' 's/border-radius: 14px/border-radius: 6px/g' styles.css

# 将完全圆形改为小圆角
sed -i '' 's/border-radius: 999px/border-radius: 4px/g' styles.css
```

### 圆角值建议

| 风格 | 小圆角 | 中等圆角 | 大圆角 | 完全圆形 |
|------|--------|---------|--------|---------|
| **圆润风格**（当前） | 8px | 10px | 14px | 999px |
| **硬朗风格**（推荐） | 2px | 4px | 6px | 0px |
| **极简风格** | 0px | 2px | 4px | 0px |

---

## Emoji 替换指南

### Emoji 使用位置统计

- **总使用次数**：10+ 处
- **主要位置**：`index.html`

### Emoji 位置映射

| 位置 | 行数 | Emoji | 用途 | 替换建议 |
|------|------|-------|------|---------|
| **编辑视图图标** | 157 | 📝 | 编辑视图标签 | SVG 图标或文字 |
| **运行视图图标** | 161 | ▶️ | 代码运行标签 | SVG 播放图标 |
| **登录角色图标** | 396-411 | 🏢👨‍🏫👤⚙️ | 角色选择卡片 | SVG 图标 |
| **功能图标** | 547-557 | 📊💬📁 | 小频道功能 | SVG 图标 |

### 替换方法

#### 方法一：使用 SVG 图标替换

**位置**：`index.html` 第 157 行

**原代码**：
```html
<span class="content-tab-icon">📝</span>
```

**替换为 SVG**：
```html
<span class="content-tab-icon">
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2"/>
    <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" stroke="currentColor" stroke-width="2"/>
  </svg>
</span>
```

#### 方法二：使用图标字体

1. **引入图标字体**（如 Font Awesome、Material Icons）：

```html
<!-- 在 index.html <head> 中添加 -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" />
```

2. **替换 Emoji**：

```html
<!-- 原代码 -->
<span class="content-tab-icon">📝</span>

<!-- 替换为 -->
<span class="content-tab-icon"><i class="fas fa-edit"></i></span>
```

#### 方法三：使用 CSS 类名 + 背景图

1. **创建图标 CSS 类**：

```css
/* 在 styles.css 中添加 */
.icon-edit::before {
  content: '';
  display: inline-block;
  width: 16px;
  height: 16px;
  background-image: url('icons/edit.svg');
  background-size: contain;
  background-repeat: no-repeat;
}
```

2. **替换 HTML**：

```html
<span class="content-tab-icon icon-edit"></span>
```

### Emoji 替换对照表

| Emoji | 用途 | SVG 图标建议 | 图标字体建议 |
|-------|------|-------------|-------------|
| 📝 | 编辑 | `<svg>` 编辑图标 | `fa-edit` |
| ▶️ | 播放/运行 | `<svg>` 播放图标 | `fa-play` |
| 🏢 | 企业 | `<svg>` 建筑图标 | `fa-building` |
| 👨‍🏫 | 教师 | `<svg>` 用户图标 | `fa-user-tie` |
| 👤 | 用户 | `<svg>` 用户图标 | `fa-user` |
| ⚙️ | 设置/管理员 | `<svg>` 齿轮图标 | `fa-cog` |
| 📊 | 数据/图表 | `<svg>` 图表图标 | `fa-chart-bar` |
| 💬 | 聊天/消息 | `<svg>` 消息图标 | `fa-comments` |
| 📁 | 文件/文件夹 | `<svg>` 文件夹图标 | `fa-folder` |

### 批量替换脚本

创建 `replace_emoji.js`：

```javascript
const fs = require('fs');
const emojiMap = {
  '📝': '<i class="fas fa-edit"></i>',
  '▶️': '<i class="fas fa-play"></i>',
  '🏢': '<i class="fas fa-building"></i>',
  '👨‍🏫': '<i class="fas fa-user-tie"></i>',
  '👤': '<i class="fas fa-user"></i>',
  '⚙️': '<i class="fas fa-cog"></i>',
  '📊': '<i class="fas fa-chart-bar"></i>',
  '💬': '<i class="fas fa-comments"></i>',
  '📁': '<i class="fas fa-folder"></i>'
};

let content = fs.readFileSync('index.html', 'utf8');
Object.keys(emojiMap).forEach(emoji => {
  content = content.replace(new RegExp(emoji, 'g'), emojiMap[emoji]);
});
fs.writeFileSync('index.html', content);
```

---

## Logo 和图标系统

### Logo 位置

#### 1. 侧边栏 Logo

**位置**：`index.html` 第 20 行、105 行、277 行

**代码**：
```html
<div class="brand__logo ai-logo">AI</div>
```

**样式位置**：`styles.css` 第 111-113 行

```css
.brand__logo {
  width: 28px;
  height: 28px;
  border-radius: 8px;  /* ← Logo 圆角 */
  display: grid;
  place-items: center;
  font-weight: 800;
  background: linear-gradient(135deg, #A0522D 0%, #8B4513 100%);
  color: #fff;
}
```

#### 2. 替换 Logo

**方法一：使用图片**

```html
<!-- 替换为图片 -->
<div class="brand__logo ai-logo">
  <img src="logo.png" alt="AI 科创平台" style="width: 100%; height: 100%; object-fit: contain;" />
</div>
```

**方法二：使用 SVG**

```html
<div class="brand__logo ai-logo">
  <svg width="28" height="28" viewBox="0 0 28 28">
    <!-- SVG 路径 -->
  </svg>
</div>
```

**方法三：修改文字和样式**

```css
.brand__logo {
  /* 修改文字 */
  content: '科创';  /* 或使用 ::before 伪元素 */
  
  /* 修改圆角（硬朗风格） */
  border-radius: 4px;  /* 从 8px 改为 4px */
  
  /* 修改背景 */
  background: #1a1a1a;  /* 纯色背景 */
}
```

### 图标系统

#### SVG 图标位置

所有 SVG 图标都在 `index.html` 中内联定义：

1. **导航图标**（第 31-52 行）
2. **功能图标**（第 244-247, 263-266 行）
3. **工具栏图标**（第 601-628 行）

#### 替换图标

**方法一：使用图标库**

1. 引入图标库（如 Heroicons、Feather Icons）：

```html
<!-- 在 <head> 中添加 -->
<script src="https://unpkg.com/heroicons@2.0.18/24/outline/index.js" type="module"></script>
```

2. 替换 SVG：

```html
<!-- 原代码 -->
<svg class="nav__icon" width="16" height="16">...</svg>

<!-- 替换为 -->
<hero-icon name="home" class="nav__icon" style="width: 16px; height: 16px;"></hero-icon>
```

**方法二：创建图标组件**

创建 `icons.js`：

```javascript
const icons = {
  home: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none">
    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" stroke="currentColor" stroke-width="2"/>
    <path d="M9 22V12h6v10" stroke="currentColor" stroke-width="2"/>
  </svg>`,
  // ... 更多图标
};

// 使用
document.querySelector('.nav__icon').innerHTML = icons.home;
```

---

## 颜色系统

### 颜色变量位置

**位置**：`styles.css` 第 1-24 行

```css
:root {
  --brand: #A0522D;        /* 品牌色：温暖褐红色 */
  --brand-600: #8B4513;    /* 品牌色深色 */
  --brand-700: #6B3410;     /* 品牌色更深 */
  --bg: #F5F1EA;            /* 背景色：米色 */
  --bg-elev: #FFFBF5;       /* 背景色提升：奶白色 */
  --text: #3E2723;          /* 文字色：深褐色 */
  --text-2: #6D4C41;        /* 文字色次要 */
  --muted: #EFE9E0;         /* 静音色 */
  --border: #D7CCC8;        /* 边框色 */
  --card: #FFFBF5;          /* 卡片色 */
  --shadow: 0 2px 10px rgba(62,39,35,.08);
}

.theme-dark {
  --bg: #0f1115;
  --bg-elev: #141821;
  --text: #e9edf4;
  /* ... */
}
```

### 快速切换颜色主题

#### 创建新颜色主题

创建 `styles-theme-blue.css`：

```css
/* 蓝色科技风格 */
:root {
  --brand: #2563eb;        /* 蓝色 */
  --brand-600: #1d4ed8;
  --brand-700: #1e40af;
  --bg: #f8fafc;
  --bg-elev: #ffffff;
  --text: #1e293b;
  --text-2: #64748b;
  --muted: #e2e8f0;
  --border: #cbd5e1;
  --card: #ffffff;
  --shadow: 0 2px 10px rgba(37,99,235,.08);
}
```

在 `index.html` 中引入：

```html
<link rel="stylesheet" href="styles.css" />
<link rel="stylesheet" href="styles-theme-blue.css" />
```

---

## 字体和排版

### 字体设置

**位置**：`styles.css` 第 33 行

```css
font-family: 'Inter', ui-sans-serif, system-ui, -apple-system, 
             Segoe UI, Roboto, Helvetica, Arial, 
             "Noto Sans", "PingFang SC", "Hiragino Sans GB", 
             "Microsoft YaHei", sans-serif;
```

### 修改字体

**引入新字体**（在 `index.html` `<head>` 中）：

```html
<!-- Google Fonts -->
<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;600;700&display=swap" rel="stylesheet">
```

**修改 CSS**：

```css
font-family: 'Roboto', 'Inter', sans-serif;
```

### 字体大小调整

主要字体大小位置：

- **Hero 标题**：`styles.css` 第 1099 行 - `clamp(46px, 7vw, 76px)`
- **页面标题**：`styles.css` 第 1105 行 - `28px`
- **按钮文字**：`styles.css` 第 376 行 - `14px`（基础按钮）

---

## 最佳实践

### 1. UI 包切换流程

```
1. 创建新的 UI 主题文件（如 styles-ui-hard.css）
2. 在 index.html 中引入（注释/取消注释）
3. 测试所有页面和功能
4. 提交到版本控制
```

### 2. 修改检查清单

- [ ] 按钮样式（圆角、颜色、大小）
- [ ] 卡片样式（圆角、阴影、边框）
- [ ] Logo 和图标（位置、大小、样式）
- [ ] Emoji 替换（全部替换为 SVG 或图标字体）
- [ ] 颜色系统（品牌色、背景色、文字色）
- [ ] 字体和排版（字体族、大小、行高）
- [ ] 响应式设计（移动端适配）
- [ ] 暗色主题（确保暗色模式正常）

### 3. 测试建议

1. **功能测试**：确保所有功能正常
2. **视觉测试**：检查所有页面的视觉效果
3. **响应式测试**：测试不同屏幕尺寸
4. **浏览器兼容性**：测试主流浏览器
5. **性能测试**：确保 UI 修改不影响性能

### 4. 版本控制

建议创建 UI 主题分支：

```bash
# 创建 UI 主题分支
git checkout -b ui-theme-hard

# 修改 UI 文件
# ...

# 提交
git add styles-ui-hard.css
git commit -m "feat: 添加硬朗风格 UI 主题"
```

---

## 快速参考

### 常用修改命令

```bash
# 批量替换圆角（硬朗风格）
sed -i '' 's/border-radius: 10px/border-radius: 4px/g' styles.css
sed -i '' 's/border-radius: 8px/border-radius: 4px/g' styles.css
sed -i '' 's/border-radius: 999px/border-radius: 4px/g' styles.css

# 查找所有 emoji
grep -n "emoji\|📝\|▶️\|🏢\|👨\|👤\|⚙️\|📊\|💬\|📁" index.html

# 查找所有圆角
grep -n "border-radius" styles.css | head -20
```

### 文件修改优先级

1. **高优先级**（影响全局）：
   - `styles.css` - 颜色变量、按钮样式
   - `index.html` - Logo、Emoji

2. **中优先级**（影响组件）：
   - `styles.css` - 卡片、表单、模态框样式

3. **低优先级**（影响细节）：
   - `styles.css` - 动画、过渡效果

---

## 总结

通过本指南，您可以：

1. ✅ **快速定位**所有 UI 元素的位置
2. ✅ **快速切换**不同的 UI 主题包
3. ✅ **批量修改**按钮圆角
4. ✅ **替换 Emoji**为更专业的图标
5. ✅ **修改 Logo**和图标系统
6. ✅ **调整颜色**和字体系统

**建议工作流程**：
1. 创建新的 UI 主题文件
2. 逐步修改各个组件
3. 测试功能完整性
4. 提交到版本控制

如有问题，请参考代码注释或联系开发团队。

---

**最后更新**：2025-11-17  
**维护者**：zhaoziwei

