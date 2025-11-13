# "我要出题"功能完善计划（配置驱动架构版）

## 📋 核心设计理念

### 设计目标
1. **配置驱动**：项目结构定义独立于代码，通过配置管理
2. **自动同步**：队友更新结构配置后，出题表单自动同步
3. **完全解耦**：出题功能和详情页渲染功能独立，互不影响
4. **向后兼容**：支持配置版本管理，旧项目仍可正常显示

### 架构图
```
┌─────────────────────────────────────────────────────────┐
│              项目结构配置系统 (ProjectStructureConfig)    │
│  ┌──────────────────────────────────────────────────┐   │
│  │  配置定义 (project-structure-config.js)         │   │
│  │  - 章节列表 (sections)                         │   │
│  │  - 章节类型 (notebook/quiz/comments/custom)    │   │
│  │  - 渲染器映射 (renderer mapping)                │   │
│  │  - 表单字段定义 (form field definitions)        │   │
│  │  - 默认内容 (default content)                   │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                    │                    │
        ┌───────────┴──────────┐        │
        │                      │        │
┌───────▼────────┐   ┌─────────▼──────┐ │
│  详情页渲染模块  │   │  出题表单模块   │ │
│  (DetailView)  │   │ (ProblemForm)  │ │
│                │   │                │ │
│  - 读取配置    │   │  - 读取配置    │ │
│  - 动态渲染    │   │  - 动态生成表单 │ │
│  - 调用渲染器  │   │  - 数据收集    │ │
└────────────────┘   └────────────────┘ │
                                      │
                              ┌───────▼──────┐
                              │  渲染器注册表  │
                              │ (RendererRegistry)│
                              │                │
                              │ - NotebookRenderer│
                              │ - QuizRenderer   │
                              │ - CommentsRenderer│
                              │ - CustomRenderer  │
                              └─────────────────┘
```

---

## 📋 当前状态分析

### 1. 项目详情页结构

项目详情页包含以下可展示部分：

#### 1.1 Notebook格式部分（使用 `renderNotebook` 渲染）
- **背景 (background)**: Markdown + Code 单元格
- **模型 (model)**: Markdown + Code 单元格  
- **模型介绍 (model-intro)**: Markdown + Code + Table 单元格
- **baseline**: Markdown + Code 单元格
- **IDEA 引导 (idea)**: Markdown + Code 单元格

#### 1.2 特殊格式部分
- **个性化检验 (personalize)**: 10道选择题（quizData数组）
- **留言区 (comments)**: 评论列表（commentsData数组）
- **小频道 (channels)**: 特殊功能模块

### 2. 当前"我要出题"功能限制

**当前表单字段**：
- ✅ 题目名称 (title)
- ✅ 分类 (category)
- ✅ 子分类 (subKey)
- ✅ 项目描述 (desc)
- ✅ 背景介绍 (background) - 仅作为文本字段

**缺失的功能**：
- ❌ 无法设置 Notebook 内容（背景、模型、IDEA等）
- ❌ 无法设置个性化检验题目
- ❌ 无法设置留言区初始内容
- ❌ 详情页内容都是硬编码，新项目会显示默认内容
- ❌ 结构更新无法自动同步到出题表单

---

## 🎯 新架构设计

### 阶段一：项目结构配置系统

#### 1.1 创建配置定义文件

**新建文件**：`project-structure-config.js`

```javascript
/**
 * 项目结构配置系统
 * 
 * 此配置定义了项目详情页的所有章节结构
 * 当队友更新此配置时，出题表单会自动同步更新
 * 
 * 配置版本：v1.0.0
 * 最后更新：2024年
 */

window.ProjectStructureConfig = {
  // 配置版本
  version: '1.0.0',
  
  // 章节定义列表
  sections: [
    {
      key: 'background',
      name: '背景',
      type: 'notebook',  // notebook | quiz | comments | custom
      required: true,    // 是否必填
      order: 1,
      description: '项目背景介绍',
      // Notebook配置
      notebookConfig: {
        defaultCells: [
          { type: 'markdown', content: '# 背景\n\n在此填写项目背景...' },
          { type: 'code', content: '# 代码示例\nprint("Hello")', language: 'python' }
        ],
        allowedCellTypes: ['markdown', 'code', 'table'],
        defaultLanguage: 'python'
      }
    },
    {
      key: 'model',
      name: '模型',
      type: 'notebook',
      required: true,
      order: 2,
      description: '模型架构介绍',
      notebookConfig: {
        defaultCells: [
          { type: 'markdown', content: '# 模型架构\n\n在此填写模型介绍...' }
        ],
        allowedCellTypes: ['markdown', 'code'],
        defaultLanguage: 'python'
      }
    },
    {
      key: 'model-intro',
      name: '模型介绍',
      type: 'notebook',
      required: false,
      order: 3,
      parent: 'model',  // 父章节，用于菜单嵌套
      description: '详细的模型介绍',
      notebookConfig: {
        defaultCells: [
          { type: 'markdown', content: '# 详细模型介绍\n\n...' }
        ],
        allowedCellTypes: ['markdown', 'code', 'table'],
        defaultLanguage: 'python'
      }
    },
    {
      key: 'baseline',
      name: 'baseline 介绍',
      type: 'notebook',
      required: false,
      order: 4,
      parent: 'model',
      description: 'Baseline对比介绍',
      notebookConfig: {
        defaultCells: [
          { type: 'markdown', content: '# Baseline介绍\n\n对比其他方法...' }
        ],
        allowedCellTypes: ['markdown', 'code'],
        defaultLanguage: 'python'
      }
    },
    {
      key: 'idea',
      name: 'IDEA 引导',
      type: 'notebook',
      required: false,
      order: 5,
      description: '优化方向建议',
      notebookConfig: {
        defaultCells: [
          { type: 'markdown', content: '# IDEA引导\n\n优化方向...' }
        ],
        allowedCellTypes: ['markdown', 'code'],
        defaultLanguage: 'python'
      }
    },
    {
      key: 'personalize',
      name: '个性化检验',
      type: 'quiz',
      required: false,
      order: 6,
      description: '知识测试题目',
      quizConfig: {
        minQuestions: 1,
        maxQuestions: 10,
        defaultQuestions: 5,
        defaultQuizData: [
          {
            question: "问题1",
            options: ["选项A", "选项B", "选项C", "选项D"],
            correct: 0
          }
        ]
      }
    },
    {
      key: 'comments',
      name: '留言区',
      type: 'comments',
      required: false,
      order: 7,
      description: '用户留言讨论区',
      commentsConfig: {
        allowInitialComments: true,
        defaultInitialComments: []
      }
    },
    {
      key: 'channels',
      name: '小频道',
      type: 'custom',
      required: false,
      order: 8,
      description: '小频道功能',
      customRenderer: 'renderChannelsSection',  // 自定义渲染器函数名
      formConfig: {
        enabled: false  // 出题表单中不显示此章节
      }
    }
  ],
  
  // 获取章节配置
  getSection(key) {
    return this.sections.find(s => s.key === key);
  },
  
  // 获取所有章节（按order排序）
  getAllSections() {
    return [...this.sections].sort((a, b) => a.order - b.order);
  },
  
  // 获取根章节（无parent的章节）
  getRootSections() {
    return this.sections.filter(s => !s.parent).sort((a, b) => a.order - b.order);
  },
  
  // 获取子章节
  getChildSections(parentKey) {
    return this.sections.filter(s => s.parent === parentKey).sort((a, b) => a.order - b.order);
  },
  
  // 获取需要在出题表单中显示的章节
  getFormSections() {
    return this.sections.filter(s => {
      // 排除custom类型且formConfig.enabled为false的章节
      if (s.type === 'custom' && s.formConfig && s.formConfig.enabled === false) {
        return false;
      }
      return true;
    }).sort((a, b) => a.order - b.order);
  },
  
  // 获取默认内容（用于新项目）
  getDefaultContent(sectionKey) {
    const section = this.getSection(sectionKey);
    if (!section) return null;
    
    switch (section.type) {
      case 'notebook':
        return section.notebookConfig?.defaultCells || [];
      case 'quiz':
        return section.quizConfig?.defaultQuizData || [];
      case 'comments':
        return section.commentsConfig?.defaultInitialComments || [];
      default:
        return null;
    }
  }
};
```

#### 1.2 在HTML中引入配置

**修改 `index.html`**：
```html
<!-- 在 app.js 之前引入配置 -->
<script src="project-structure-config.js"></script>
<script src="app.js"></script>
```

---

### 阶段二：渲染器注册系统

#### 2.1 创建渲染器注册表

**在 `app.js` 中添加**：

```javascript
/**
 * 渲染器注册表
 * 将章节类型映射到对应的渲染函数
 */
window.RendererRegistry = {
  // Notebook渲染器
  notebook: function(sectionKey, content, project) {
    const sectionConfig = window.ProjectStructureConfig.getSection(sectionKey);
    const cells = content || sectionConfig?.notebookConfig?.defaultCells || [];
    renderNotebook('detailContent', cells);
  },
  
  // 个性化检验渲染器
  quiz: function(sectionKey, content, project) {
    const sectionConfig = window.ProjectStructureConfig.getSection(sectionKey);
    const quizData = content || sectionConfig?.quizConfig?.defaultQuizData || [];
    renderPersonalizeSection(document.getElementById('detailContent'), quizData);
  },
  
  // 留言区渲染器
  comments: function(sectionKey, content, project) {
    const sectionConfig = window.ProjectStructureConfig.getSection(sectionKey);
    const initialComments = content || sectionConfig?.commentsConfig?.defaultInitialComments || [];
    renderCommentsSection(document.getElementById('detailContent'), initialComments);
  },
  
  // 自定义渲染器（通过函数名调用）
  custom: function(sectionKey, content, project) {
    const sectionConfig = window.ProjectStructureConfig.getSection(sectionKey);
    const rendererName = sectionConfig?.customRenderer;
    
    if (rendererName && typeof window[rendererName] === 'function') {
      window[rendererName](document.getElementById('detailContent'), content, project);
    } else {
      console.warn(`[RendererRegistry] 自定义渲染器 "${rendererName}" 未找到`);
    }
  },
  
  // 注册新的渲染器
  register(type, renderer) {
    if (typeof renderer !== 'function') {
      console.error(`[RendererRegistry] 渲染器必须是函数`);
      return;
    }
    this[type] = renderer;
    console.log(`[RendererRegistry] 已注册渲染器: ${type}`);
  }
};
```

---

### 阶段三：详情页渲染改造

#### 3.1 修改 `buildDetailMenu` 函数

**位置**：`app.js` 第843行

**新实现**：
```javascript
function buildDetailMenu(project) {
  const menu = document.getElementById('detailMenu');
  menu.innerHTML = '';
  
  // 从配置获取章节结构
  const rootSections = window.ProjectStructureConfig.getRootSections();
  
  const ul = document.createElement('ul');
  ul.className = 'nav__list';
  
  rootSections.forEach(section => {
    const li = document.createElement('li');
    const hasChildren = window.ProjectStructureConfig.getChildSections(section.key).length > 0;
    
    li.innerHTML = `<button class="nav__item" data-sec="${section.key}">
      <span class="caret">${hasChildren ? '▸' : '◆'}</span>${section.name}
    </button>`;
    
    const btn = li.querySelector('button');
    
    if (hasChildren) {
      // 有子章节
      btn.addEventListener('click', () => {
        const opened = li.querySelector('.sublist');
        li.querySelector('.caret').textContent = opened ? '▸' : '▾';
        
        if (opened) {
          opened.remove();
          return;
        }
        
        const sub = document.createElement('ul');
        sub.className = 'sublist';
        
        const childSections = window.ProjectStructureConfig.getChildSections(section.key);
        childSections.forEach(childSection => {
          const sli = document.createElement('li');
          sli.innerHTML = `<button class="subitem" data-sec="${childSection.key}">${childSection.name}</button>`;
          sli.querySelector('button').addEventListener('click', (e) => {
            e.stopPropagation();
            renderDetailSection(childSection.key, project);
            history.pushState(
              { view: 'detail', id: project.id, section: childSection.key },
              '',
              `#project/${project.id}/${childSection.key}`
            );
          });
          sub.appendChild(sli);
        });
        
        li.appendChild(sub);
      });
    } else {
      // 无子章节
      btn.addEventListener('click', () => {
        renderDetailSection(section.key, project);
        history.pushState(
          { view: 'detail', id: project.id, section: section.key },
          '',
          `#project/${project.id}/${section.key}`
        );
      });
    }
    
    ul.appendChild(li);
  });
  
  menu.appendChild(ul);
}
```

#### 3.2 修改 `renderDetailSection` 函数

**位置**：`app.js` 第1423行

**新实现**：
```javascript
function renderDetailSection(key, project = null) {
  const wrap = document.getElementById('detailContent');
  const videoArea = document.querySelector('.detail__video');
  
  // 获取当前项目（如果未传入）
  if (!project) {
    project = getCurrentProject();
  }
  
  // 从配置获取章节定义
  const sectionConfig = window.ProjectStructureConfig.getSection(key);
  if (!sectionConfig) {
    console.warn(`[renderDetailSection] 章节 "${key}" 未在配置中找到`);
    wrap.innerHTML = '<p>章节未找到</p>';
    return;
  }
  
  // 更新当前分区
  currentSection = key;
  
  // 处理视频区域显示/隐藏
  if (sectionConfig.type === 'quiz' || sectionConfig.type === 'comments') {
    if (videoArea) videoArea.style.display = 'none';
  } else {
    if (videoArea) videoArea.style.display = '';
  }
  
  // 从项目数据获取内容，如果没有则使用默认内容
  let content = null;
  if (project?.detailContent?.[key]) {
    content = project.detailContent[key];
  } else {
    // 使用配置中的默认内容
    content = window.ProjectStructureConfig.getDefaultContent(key);
  }
  
  // 根据章节类型调用对应的渲染器
  const renderer = window.RendererRegistry[sectionConfig.type];
  if (renderer && typeof renderer === 'function') {
    try {
      renderer(key, content, project);
    } catch (error) {
      console.error(`[renderDetailSection] 渲染章节 "${key}" 时出错:`, error);
      wrap.innerHTML = `<p>渲染出错: ${error.message}</p>`;
    }
  } else {
    console.error(`[renderDetailSection] 未找到类型 "${sectionConfig.type}" 的渲染器`);
    wrap.innerHTML = '<p>渲染器未找到</p>';
  }
}

// 新增：获取当前项目
function getCurrentProject() {
  const projectId = window.currentProjectId;
  if (!projectId) return null;
  
  const projects = window.projects || [];
  return projects.find(p => p.id === projectId) || null;
}
```

---

### 阶段四：出题表单动态生成

#### 4.1 修改表单HTML结构

**位置**：`index.html` 第288-401行

**新增动态表单容器**：
```html
<form id="createProblemForm" class="problem-creation-form">
  <!-- 基本信息（保持不变） -->
  <div class="form-section">
    <h2 class="form-section-title">基本信息</h2>
    <!-- 现有的基础字段 -->
  </div>
  
  <!-- 动态生成的详情内容表单 -->
  <div id="detailContentForm" class="form-section">
    <h2 class="form-section-title">详情内容</h2>
    <p class="form-section-desc">填写项目的详细内容，未填写的部分将使用默认内容</p>
    
    <!-- 动态生成的章节编辑器将插入这里 -->
    <div id="dynamicSectionsContainer"></div>
  </div>
  
  <!-- 表单操作按钮 -->
  <div class="form-actions">
    <button type="button" class="btn btn--ghost" id="cancelCreateBtn">取消</button>
    <button type="submit" class="btn btn--primary">提交审核</button>
  </div>
</form>
```

#### 4.2 创建表单生成器

**在 `app.js` 的 ProblemCreationModule 中添加**：

```javascript
/**
 * 动态生成详情内容表单
 * 基于 ProjectStructureConfig 配置自动生成
 */
function generateDetailContentForm() {
  const container = qs('#dynamicSectionsContainer', createProblemForm);
  if (!container) {
    console.warn(`[${MODULE_NAME}] 动态表单容器未找到`);
    return;
  }
  
  container.innerHTML = '';
  
  // 从配置获取需要在表单中显示的章节
  const formSections = window.ProjectStructureConfig.getFormSections();
  
  formSections.forEach(section => {
    const sectionEditor = createSectionEditor(section);
    if (sectionEditor) {
      container.appendChild(sectionEditor);
    }
  });
  
  console.log(`[${MODULE_NAME}] 已生成 ${formSections.length} 个章节编辑器`);
}

/**
 * 创建单个章节编辑器
 */
function createSectionEditor(sectionConfig) {
  const sectionDiv = document.createElement('div');
  sectionDiv.className = 'form-section-item';
  sectionDiv.dataset.sectionKey = sectionConfig.key;
  
  const header = document.createElement('div');
  header.className = 'form-section-item-header';
  header.innerHTML = `
    <h3 class="form-section-item-title">
      ${sectionConfig.name}
      ${sectionConfig.required ? '<span class="required">*</span>' : ''}
    </h3>
    <p class="form-section-item-desc">${sectionConfig.description || ''}</p>
  `;
  sectionDiv.appendChild(header);
  
  const content = document.createElement('div');
  content.className = 'form-section-item-content';
  
  // 根据章节类型创建对应的编辑器
  switch (sectionConfig.type) {
    case 'notebook':
      content.appendChild(createNotebookEditor(sectionConfig));
      break;
    case 'quiz':
      content.appendChild(createQuizEditor(sectionConfig));
      break;
    case 'comments':
      content.appendChild(createCommentsEditor(sectionConfig));
      break;
    default:
      console.warn(`[${MODULE_NAME}] 未支持的章节类型: ${sectionConfig.type}`);
      return null;
  }
  
  sectionDiv.appendChild(content);
  return sectionDiv;
}

/**
 * 创建Notebook编辑器
 */
function createNotebookEditor(sectionConfig) {
  const editor = document.createElement('div');
  editor.className = 'notebook-editor';
  editor.dataset.sectionKey = sectionConfig.key;
  
  const cellsContainer = document.createElement('div');
  cellsContainer.className = 'notebook-cells-container';
  editor.appendChild(cellsContainer);
  
  // 添加默认单元格
  const defaultCells = sectionConfig.notebookConfig?.defaultCells || [];
  defaultCells.forEach((cellData, index) => {
    const cellEditor = createNotebookCellEditor(cellData, index);
    cellsContainer.appendChild(cellEditor);
  });
  
  // 添加单元格按钮
  const actions = document.createElement('div');
  actions.className = 'notebook-editor-actions';
  actions.innerHTML = `
    <button type="button" class="btn btn--ghost btn--small add-markdown-cell">+ Markdown</button>
    <button type="button" class="btn btn--ghost btn--small add-code-cell">+ Code</button>
  `;
  
  actions.querySelector('.add-markdown-cell').addEventListener('click', () => {
    const cellEditor = createNotebookCellEditor({ type: 'markdown', content: '' }, cellsContainer.children.length);
    cellsContainer.appendChild(cellEditor);
  });
  
  actions.querySelector('.add-code-cell').addEventListener('click', () => {
    const cellEditor = createNotebookCellEditor({
      type: 'code',
      content: '',
      language: sectionConfig.notebookConfig?.defaultLanguage || 'python'
    }, cellsContainer.children.length);
    cellsContainer.appendChild(cellEditor);
  });
  
  editor.appendChild(actions);
  return editor;
}

/**
 * 创建Notebook单元格编辑器
 */
function createNotebookCellEditor(cellData, index) {
  const cellDiv = document.createElement('div');
  cellDiv.className = 'notebook-cell-editor';
  cellDiv.dataset.cellIndex = index;
  cellDiv.dataset.cellType = cellData.type;
  
  const header = document.createElement('div');
  header.className = 'notebook-cell-editor-header';
  
  const typeSelect = document.createElement('select');
  typeSelect.className = 'cell-type-select';
  typeSelect.innerHTML = `
    <option value="markdown" ${cellData.type === 'markdown' ? 'selected' : ''}>Markdown</option>
    <option value="code" ${cellData.type === 'code' ? 'selected' : ''}>Code</option>
  `;
  
  const languageSelect = document.createElement('select');
  languageSelect.className = 'cell-language-select';
  languageSelect.style.display = cellData.type === 'code' ? 'inline-block' : 'none';
  languageSelect.innerHTML = `
    <option value="python" ${cellData.language === 'python' ? 'selected' : ''}>Python</option>
    <option value="javascript" ${cellData.language === 'javascript' ? 'selected' : ''}>JavaScript</option>
  `;
  
  const deleteBtn = document.createElement('button');
  deleteBtn.type = 'button';
  deleteBtn.className = 'btn btn--ghost btn--tiny delete-cell-btn';
  deleteBtn.textContent = '删除';
  deleteBtn.addEventListener('click', () => cellDiv.remove());
  
  header.appendChild(typeSelect);
  header.appendChild(languageSelect);
  header.appendChild(deleteBtn);
  
  const contentTextarea = document.createElement('textarea');
  contentTextarea.className = 'cell-content-input';
  contentTextarea.value = cellData.content || '';
  contentTextarea.placeholder = cellData.type === 'markdown' 
    ? '输入 Markdown 内容...' 
    : '输入代码...';
  contentTextarea.rows = 5;
  
  typeSelect.addEventListener('change', (e) => {
    cellDiv.dataset.cellType = e.target.value;
    languageSelect.style.display = e.target.value === 'code' ? 'inline-block' : 'none';
  });
  
  languageSelect.addEventListener('change', (e) => {
    cellDiv.dataset.language = e.target.value;
  });
  
  cellDiv.appendChild(header);
  cellDiv.appendChild(contentTextarea);
  
  return cellDiv;
}

/**
 * 创建个性化检验编辑器
 */
function createQuizEditor(sectionConfig) {
  const editor = document.createElement('div');
  editor.className = 'quiz-editor';
  editor.dataset.sectionKey = sectionConfig.key;
  
  const questionsContainer = document.createElement('div');
  questionsContainer.className = 'quiz-questions-container';
  editor.appendChild(questionsContainer);
  
  // 添加默认题目
  const defaultQuestions = sectionConfig.quizConfig?.defaultQuizData || [];
  defaultQuestions.forEach((questionData, index) => {
    const questionEditor = createQuizQuestionEditor(questionData, index);
    questionsContainer.appendChild(questionEditor);
  });
  
  // 添加题目按钮
  const addBtn = document.createElement('button');
  addBtn.type = 'button';
  addBtn.className = 'btn btn--ghost btn--small add-question-btn';
  addBtn.textContent = '+ 添加题目';
  addBtn.addEventListener('click', () => {
    const maxQuestions = sectionConfig.quizConfig?.maxQuestions || 10;
    if (questionsContainer.children.length >= maxQuestions) {
      alert(`最多只能添加 ${maxQuestions} 道题目`);
      return;
    }
    const questionEditor = createQuizQuestionEditor({
      question: '',
      options: ['', '', '', ''],
      correct: 0
    }, questionsContainer.children.length);
    questionsContainer.appendChild(questionEditor);
  });
  
  editor.appendChild(addBtn);
  return editor;
}

/**
 * 创建题目编辑器
 */
function createQuizQuestionEditor(questionData, index) {
  const questionDiv = document.createElement('div');
  questionDiv.className = 'quiz-question-editor';
  questionDiv.dataset.questionIndex = index;
  
  const header = document.createElement('div');
  header.className = 'quiz-question-editor-header';
  header.innerHTML = `<span class="question-number">第 ${index + 1} 题</span>`;
  
  const deleteBtn = document.createElement('button');
  deleteBtn.type = 'button';
  deleteBtn.className = 'btn btn--ghost btn--tiny delete-question-btn';
  deleteBtn.textContent = '删除';
  deleteBtn.addEventListener('click', () => questionDiv.remove());
  header.appendChild(deleteBtn);
  
  const questionInput = document.createElement('textarea');
  questionInput.className = 'question-input';
  questionInput.value = questionData.question || '';
  questionInput.placeholder = '输入问题...';
  questionInput.rows = 2;
  
  const optionsContainer = document.createElement('div');
  optionsContainer.className = 'quiz-options-container';
  
  questionData.options.forEach((option, optIndex) => {
    const optionDiv = document.createElement('div');
    optionDiv.className = 'quiz-option-editor';
    
    const optionLabel = document.createElement('label');
    optionLabel.className = 'option-label';
    optionLabel.textContent = String.fromCharCode(65 + optIndex);
    
    const optionInput = document.createElement('input');
    optionInput.type = 'text';
    optionInput.className = 'option-input';
    optionInput.value = option || '';
    optionInput.placeholder = `选项 ${String.fromCharCode(65 + optIndex)}`;
    
    const correctRadio = document.createElement('input');
    correctRadio.type = 'radio';
    correctRadio.name = `correct_${index}`;
    correctRadio.value = optIndex;
    correctRadio.checked = optIndex === questionData.correct;
    
    optionDiv.appendChild(correctRadio);
    optionDiv.appendChild(optionLabel);
    optionDiv.appendChild(optionInput);
    optionsContainer.appendChild(optionDiv);
  });
  
  questionDiv.appendChild(header);
  questionDiv.appendChild(questionInput);
  questionDiv.appendChild(optionsContainer);
  
  return questionDiv;
}

/**
 * 创建留言区编辑器（可选）
 */
function createCommentsEditor(sectionConfig) {
  const editor = document.createElement('div');
  editor.className = 'comments-editor';
  editor.innerHTML = `
    <p class="form-hint">留言区将在项目发布后自动创建，无需在此设置初始内容。</p>
  `;
  return editor;
}
```

#### 4.3 修改数据收集函数

**修改 `collectFormData` 函数**：

```javascript
function collectFormData() {
  const baseData = {
    title: qs('#problemTitle', createProblemForm)?.value.trim() || '',
    category: qs('#problemCategory', createProblemForm)?.value || '',
    subKey: qs('#problemSubKey', createProblemForm)?.value.trim() || '',
    desc: qs('#problemDesc', createProblemForm)?.value.trim() || ''
  };
  
  // 收集详情内容
  const detailContent = {};
  const formSections = window.ProjectStructureConfig.getFormSections();
  
  formSections.forEach(section => {
    const sectionData = collectSectionData(section);
    if (sectionData !== null) {
      detailContent[section.key] = sectionData;
    }
  });
  
  return {
    ...baseData,
    detailContent: Object.keys(detailContent).length > 0 ? detailContent : null
  };
}

function collectSectionData(sectionConfig) {
  switch (sectionConfig.type) {
    case 'notebook':
      return collectNotebookSectionData(sectionConfig.key);
    case 'quiz':
      return collectQuizSectionData(sectionConfig.key);
    case 'comments':
      return null; // 留言区不需要在表单中收集
    default:
      return null;
  }
}

function collectNotebookSectionData(sectionKey) {
  const editor = qs(`.notebook-editor[data-section-key="${sectionKey}"]`, createProblemForm);
  if (!editor) return null;
  
  const cells = [];
  const cellEditors = editor.querySelectorAll('.notebook-cell-editor');
  
  cellEditors.forEach(cellEl => {
    const type = cellEl.dataset.cellType;
    const content = cellEl.querySelector('.cell-content-input')?.value.trim() || '';
    const language = cellEl.dataset.language || 'python';
    
    if (content) {
      cells.push({ type, content, language });
    }
  });
  
  return cells.length > 0 ? cells : null;
}

function collectQuizSectionData(sectionKey) {
  const editor = qs(`.quiz-editor[data-section-key="${sectionKey}"]`, createProblemForm);
  if (!editor) return null;
  
  const questions = [];
  const questionEditors = editor.querySelectorAll('.quiz-question-editor');
  
  questionEditors.forEach(qEl => {
    const question = qEl.querySelector('.question-input')?.value.trim();
    const options = [];
    const optionInputs = qEl.querySelectorAll('.option-input');
    
    optionInputs.forEach(opt => {
      const value = opt.value.trim();
      if (value) options.push(value);
    });
    
    const correctRadio = qEl.querySelector('input[type="radio"]:checked');
    const correct = correctRadio ? parseInt(correctRadio.value) : 0;
    
    if (question && options.length === 4) {
      questions.push({ question, options, correct });
    }
  });
  
  return questions.length > 0 ? questions : null;
}
```

#### 4.4 初始化表单生成

**修改 `initForm` 函数**：

```javascript
function initForm() {
  if (!createProblemForm) {
    console.warn(`[${MODULE_NAME}] 表单元素未找到`);
    return;
  }
  
  // 动态生成详情内容表单
  generateDetailContentForm();
  
  // 绑定提交事件
  createProblemForm.addEventListener('submit', handleFormSubmit);
  console.log(`[${MODULE_NAME}] 表单事件已绑定`);
}
```

---

### 阶段五：配置热更新机制

#### 5.1 配置版本管理

**在配置文件中添加版本检查**：

```javascript
window.ProjectStructureConfig = {
  version: '1.0.0',
  
  // 检查配置版本
  checkVersion() {
    const storedVersion = localStorage.getItem('project_structure_config_version');
    if (storedVersion && storedVersion !== this.version) {
      console.log(`[ProjectStructureConfig] 配置版本更新: ${storedVersion} -> ${this.version}`);
      // 可以在这里执行数据迁移逻辑
      this.migrateConfig(storedVersion, this.version);
    }
    localStorage.setItem('project_structure_config_version', this.version);
  },
  
  // 配置迁移（如果需要）
  migrateConfig(oldVersion, newVersion) {
    // 处理版本迁移逻辑
    console.log(`[ProjectStructureConfig] 执行配置迁移...`);
  },
  
  // ... 其他配置 ...
};

// 初始化时检查版本
if (window.ProjectStructureConfig) {
  window.ProjectStructureConfig.checkVersion();
}
```

#### 5.2 配置更新监听

**添加配置更新事件**：

```javascript
// 当配置更新时，重新生成表单
window.addEventListener('projectStructureConfigUpdated', () => {
  console.log('[ProblemCreation] 检测到配置更新，重新生成表单');
  
  // 如果当前在出题页面，重新生成表单
  const createView = qs('#create-view');
  if (createView && createView.classList.contains('active')) {
    const module = window.ProblemCreation;
    if (module && typeof module.regenerateForm === 'function') {
      module.regenerateForm();
    }
  }
});
```

---

## 🔒 解耦和独立性保证

### 1. 代码隔离

- **配置文件独立**：`project-structure-config.js` 独立文件，可以单独更新
- **渲染器注册表独立**：渲染器可以独立注册和更新
- **表单生成器独立**：出题表单生成逻辑独立，不影响详情页渲染

### 2. 错误隔离

```javascript
// 详情页渲染错误不影响出题表单
function renderDetailSection(key, project) {
  try {
    // 渲染逻辑
  } catch (error) {
    console.error(`[renderDetailSection] 错误:`, error);
    // 显示错误提示，但不影响其他功能
    wrap.innerHTML = `<p>渲染出错，请刷新页面重试</p>`;
  }
}

// 表单生成错误不影响详情页
function generateDetailContentForm() {
  try {
    // 表单生成逻辑
  } catch (error) {
    console.error(`[ProblemCreation] 表单生成错误:`, error);
    // 显示错误提示，但不影响详情页
    container.innerHTML = `<p>表单生成出错，请刷新页面重试</p>`;
  }
}
```

### 3. 数据隔离

- 项目数据存储在独立的 `detailContent` 字段
- 配置数据存储在独立的配置文件中
- 两者互不影响

---

## 📊 实施步骤

### 第一步：创建配置系统（2-3小时）
1. 创建 `project-structure-config.js` 文件
2. 定义完整的章节配置
3. 在HTML中引入配置文件

### 第二步：创建渲染器注册表（1-2小时）
1. 创建 `RendererRegistry` 对象
2. 注册现有渲染器（notebook, quiz, comments）
3. 支持自定义渲染器注册

### 第三步：改造详情页渲染（2-3小时）
1. 修改 `buildDetailMenu` 使用配置
2. 修改 `renderDetailSection` 使用配置和渲染器
3. 添加 `getCurrentProject` 辅助函数
4. 测试现有项目显示正常

### 第四步：实现动态表单生成（3-4小时）
1. 创建表单生成器函数
2. 实现各类型编辑器（Notebook、Quiz等）
3. 实现数据收集函数
4. 修改 `initForm` 调用表单生成

### 第五步：测试和优化（1-2小时）
1. 功能测试
2. 兼容性测试
3. 错误处理测试
4. UI/UX优化

**总计预计时间**：9-14小时

---

## ✅ 优势总结

1. **自动同步**：队友更新配置后，出题表单自动更新
2. **完全解耦**：出题功能和详情页功能独立，互不影响
3. **易于扩展**：添加新章节只需更新配置，无需修改代码
4. **向后兼容**：现有项目继续使用默认内容，不受影响
5. **错误隔离**：一个功能出错不影响另一个功能
6. **配置驱动**：结构定义与代码分离，易于维护

---

**文档创建时间**：2024年
**最后更新**：2024年
**维护者**：zhaoziwei
