# 协作开发工作流程 (Workflow)

> **重要提示**: 本文档是给 **AI Agent (Cursor)** 看的，用于指导协作开发流程。请严格按照此流程执行，避免代码冲突和功能损坏。

---

## 📋 核心原则

1. **新功能开发前必须先合并**: 每次开始新功能前，必须先将两个开发分支（`zhaoziwei` 和 `wangmingxuan`）合并到主分支
2. **功能验证后再分支**: 合并后必须测试确保所有功能正常，才能创建新分支
3. **独立开发，数据接口交互**: 各自功能模块保持独立，只通过数据接口（localStorage、Custom Events）交互
4. **避免全局污染**: 使用 IIFE 封装模块，避免全局变量冲突

---

## 🔄 标准工作流程

### 阶段 1: 准备新功能开发

#### 步骤 1.1: 检查当前状态
```bash
# 1. 查看当前分支
git branch

# 2. 检查工作区状态
git status

# 3. 如果有未提交的更改，先提交或暂存
git add .
git commit -m "描述你的更改"
```

#### 步骤 1.2: 切换到主分支并拉取最新代码
```bash
# 切换到 main 分支
git checkout main

# 拉取远程最新代码
git pull origin main
```

#### 步骤 1.3: 合并队友的分支
```bash
# 合并 wangmingxuan 分支（如果当前是 zhaoziwei 开发者）
git merge origin/wangmingxuan

# 或者合并 zhaoziwei 分支（如果当前是 wangmingxuan 开发者）
git merge origin/zhaoziwei
```

**⚠️ 如果出现冲突**:
1. **不要自动解决冲突**，先查看冲突文件
2. **通知用户**，让用户决定如何解决
3. 冲突解决后：
   ```bash
   git add .
   git commit -m "解决合并冲突"
   ```

#### 步骤 1.4: 测试合并后的代码
```bash
# 启动本地服务器
python3 -m http.server 8000

# 在浏览器中测试：
# 1. 登录功能（所有角色）
# 2. 项目浏览功能
# 3. 出题功能（如果已实现）
# 4. 审核功能（如果已实现）
# 5. 其他已实现的功能
```

**✅ 必须确保**:
- [ ] 所有现有功能正常工作
- [ ] 没有 JavaScript 错误（检查浏览器控制台）
- [ ] 页面可以正常加载和切换
- [ ] 数据可以正常保存和读取

#### 步骤 1.5: 推送到远程主分支
```bash
# 确认测试通过后，推送到远程
git push origin main
```

---

### 阶段 2: 创建新功能分支

#### 步骤 2.1: 创建并切换到新分支
```bash
# 基于最新的 main 分支创建新分支
git checkout -b zhaoziwei-feature-xxx
# 或
git checkout -b wangmingxuan-feature-xxx

# 分支命名规范：
# - zhaoziwei-feature-功能名
# - wangmingxuan-feature-功能名
# 例如：zhaoziwei-feature-problem-creation
```

#### 步骤 2.2: 推送新分支到远程
```bash
git push -u origin zhaoziwei-feature-xxx
```

---

### 阶段 3: 开发新功能

#### 步骤 3.1: 开发前检查清单
- [ ] 确认当前分支正确
- [ ] 确认主分支已合并最新代码
- [ ] 确认本地服务器运行正常

#### 步骤 3.2: 代码开发规范

**1. 模块封装（必须）**
```javascript
// ✅ 正确：使用 IIFE 封装
(function() {
  'use strict';
  
  const MODULE_NAME = 'YourModule';
  
  // 模块内部代码
  
  // 只暴露必要的接口
  window.YourModule = {
    init: init,
    // 其他公共方法
  };
})();

// ❌ 错误：全局变量污染
var globalVar = 'something'; // 不要这样做
```

**2. 数据接口交互**
```javascript
// ✅ 正确：通过 localStorage 和 Custom Events
// 保存数据
localStorage.setItem('key', JSON.stringify(data));
window.dispatchEvent(new CustomEvent('dataUpdated'));

// 读取数据
const data = JSON.parse(localStorage.getItem('key') || '[]');

// 监听更新
window.addEventListener('dataUpdated', handleUpdate);

// ❌ 错误：直接修改其他模块的内部变量
window.otherModule.internalVar = 'something'; // 不要这样做
```

**3. DOM 元素选择**
```javascript
// ✅ 正确：使用作用域内的选择器
const createView = document.querySelector('#create-view');
const form = createView?.querySelector('#createProblemForm');

// ❌ 错误：假设元素一定存在
const form = document.querySelector('#createProblemForm');
form.addEventListener(...); // 可能报错
```

#### 步骤 3.3: 开发过程中的测试
- 每完成一个小功能就测试一次
- 检查浏览器控制台是否有错误
- 确认功能独立，不影响其他模块

---

### 阶段 4: 提交代码

#### 步骤 4.1: 提交前检查
```bash
# 1. 检查更改的文件
git status

# 2. 检查代码语法（JavaScript）
node -c app.js

# 3. 检查是否有 linter 错误
# （如果项目配置了 linter）
```

#### 步骤 4.2: 提交代码
```bash
# 添加更改
git add .

# 提交（使用清晰的提交信息）
git commit -m "功能: 描述你实现的功能

- 具体更改点 1
- 具体更改点 2
- 具体更改点 3"

# 推送到远程
git push
```

**提交信息规范**:
- 第一行：简短描述（50字以内）
- 空一行
- 详细说明（可选）：列出主要更改点

---

### 阶段 5: 功能完成后合并

#### 步骤 5.1: 最终测试
- [ ] 新功能正常工作
- [ ] 不影响现有功能
- [ ] 没有控制台错误
- [ ] 代码符合规范

#### 步骤 5.2: 创建 Pull Request（可选）
如果使用 GitHub，可以创建 PR 让队友审查。

#### 步骤 5.3: 合并到主分支
```bash
# 切换到 main 分支
git checkout main

# 拉取最新代码
git pull origin main

# 合并功能分支
git merge zhaoziwei-feature-xxx

# 测试合并后的代码
# （重复阶段 1.4 的测试步骤）

# 推送到远程
git push origin main
```

---

## ⚠️ 重要注意事项（给 AI Agent）

### 1. 分支管理
- **永远不要**直接在主分支（`main`）上开发新功能
- **永远不要**强制推送（`git push --force`）到共享分支
- **永远不要**删除队友的分支

### 2. 代码合并
- **合并前必须测试**: 合并后立即启动服务器测试
- **冲突处理**: 遇到冲突时，**不要自动解决**，先通知用户
- **合并后验证**: 合并后必须验证所有功能正常

### 3. 模块独立性
- **不要修改**队友的模块代码（除非明确要求）
- **不要直接访问**其他模块的内部变量或函数
- **只通过接口交互**: 使用 localStorage、Custom Events、全局暴露的接口

### 4. 全局变量
- **避免全局污染**: 使用 IIFE 封装所有代码
- **命名空间**: 如果必须暴露全局变量，使用命名空间（如 `window.ProblemCreation`）
- **检查冲突**: 暴露全局变量前，检查是否已存在

### 5. DOM 操作
- **元素存在性检查**: 使用可选链（`?.`）或 `if` 检查元素是否存在
- **事件委托**: 优先使用事件委托，避免内存泄漏
- **清理事件监听器**: 页面切换时清理不需要的监听器

### 6. 数据存储
- **localStorage 键名**: 使用统一的键名规范（如 `ai_platform_projects`）
- **数据格式**: 使用 JSON 序列化/反序列化
- **数据验证**: 读取数据时验证格式，提供默认值

### 7. 错误处理
- **语法检查**: 每次修改后运行 `node -c app.js` 检查语法
- **控制台检查**: 开发过程中经常检查浏览器控制台
- **优雅降级**: 功能失败时不影响其他功能

### 8. 测试流程
- **功能测试**: 每个功能完成后立即测试
- **集成测试**: 合并后测试所有功能的集成
- **回归测试**: 确保新功能不影响现有功能

---

## 🔍 常见问题排查

### 问题 1: 合并后功能不工作
```bash
# 1. 检查浏览器控制台错误
# 2. 检查 JavaScript 语法
node -c app.js

# 3. 检查是否有未提交的更改
git status

# 4. 检查分支是否正确
git branch
```

### 问题 2: 代码冲突
```bash
# 1. 查看冲突文件
git status

# 2. 打开冲突文件，查找 <<<<<<< 标记
# 3. 手动解决冲突（保留双方需要的代码）
# 4. 标记为已解决
git add <冲突文件>
git commit -m "解决合并冲突"
```

### 问题 3: 功能互相影响
- 检查是否使用了全局变量
- 检查事件监听器是否正确清理
- 检查 DOM 选择器是否唯一
- 检查 localStorage 键名是否冲突

### 问题 4: 页面无法加载
```bash
# 1. 检查服务器是否运行
curl http://localhost:8000

# 2. 检查文件是否存在
ls -la index.html app.js styles.css

# 3. 检查浏览器控制台错误
```

---

## 📝 开发检查清单

### 开始新功能前
- [ ] 已切换到 main 分支
- [ ] 已拉取最新代码
- [ ] 已合并队友的分支
- [ ] 已测试合并后的代码
- [ ] 已创建新功能分支

### 开发过程中
- [ ] 代码使用 IIFE 封装
- [ ] 没有全局变量污染
- [ ] 通过接口与其他模块交互
- [ ] 元素存在性检查
- [ ] 错误处理完善

### 提交代码前
- [ ] 功能正常工作
- [ ] 没有控制台错误
- [ ] 语法检查通过
- [ ] 不影响其他功能
- [ ] 提交信息清晰

### 合并到主分支前
- [ ] 已完成最终测试
- [ ] 队友已审查（如需要）
- [ ] 所有功能正常
- [ ] 代码符合规范

---

## 🎯 快速参考命令

```bash
# 查看当前分支
git branch

# 切换到主分支
git checkout main

# 拉取最新代码
git pull origin main

# 合并队友分支
git merge origin/wangmingxuan  # 或 origin/zhaoziwei

# 创建新分支
git checkout -b zhaoziwei-feature-xxx

# 提交代码
git add .
git commit -m "功能: 描述"
git push

# 启动服务器
python3 -m http.server 8000

# 检查语法
node -c app.js
```

---

## 📞 协作沟通

- **遇到冲突**: 立即通知用户，不要自动解决
- **功能异常**: 详细记录错误信息，包括浏览器控制台输出
- **不确定时**: 询问用户，不要猜测
- **重大更改**: 先与用户确认，再执行

---

**最后更新**: 2024年
**维护者**: zhaoziwei & wangmingxuan

