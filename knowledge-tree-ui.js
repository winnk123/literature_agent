/**
 * 知识树UI组件模块
 * 包含TreeView、NodeDrawer、ProgressBadge等组件的渲染和交互逻辑
 */

(function() {
  'use strict';

  const qs = (s, r = document) => r.querySelector(s);
  const qsa = (s, r = document) => Array.from(r.querySelectorAll(s));

  // ==================== 全局状态 ====================
  let currentTree = null;
  let selectedNode = null;
  let isAdminMode = false;

  // ==================== 初始化 ====================

  /**
   * 初始化知识树UI
   */
  function initKnowledgeTreeUI() {
    // 加载知识树数据
    if (typeof knowledgeTree !== 'undefined') {
      currentTree = KnowledgeTreeCore.loadKnowledgeTree() || JSON.parse(JSON.stringify(knowledgeTree));
    } else if (typeof window.knowledgeTree !== 'undefined') {
      currentTree = KnowledgeTreeCore.loadKnowledgeTree() || JSON.parse(JSON.stringify(window.knowledgeTree));
    } else {
      // 尝试从localStorage加载
      currentTree = KnowledgeTreeCore.loadKnowledgeTree();
      if (!currentTree) {
        console.error('知识树数据未加载，请刷新页面');
        return;
      }
    }

    // 更新树状态
    KnowledgeTreeCore.updateTreeStatus(currentTree);
    
    // 渲染树视图
    renderTreeView();
    
    // 渲染进度概览
    renderProgressOverview();
    
    // 渲染本周任务
    renderWeeklyTasks();
    
    // 绑定事件
    bindEvents();
  }

  // ==================== TreeView 渲染 ====================

  /**
   * 渲染知识树视图
   */
  function renderTreeView() {
    const container = qs('#knowledgeTreeContainer');
    if (!container) return;

    container.innerHTML = '';
    
    const treeElement = createTreeNode(currentTree, 0);
    container.appendChild(treeElement);
  }

  /**
   * 创建树节点元素（递归）
   */
  function createTreeNode(node, depth = 0) {
    const nodeEl = document.createElement('div');
    nodeEl.className = `tree-node tree-node--${node.type} tree-node--depth-${depth}`;
    nodeEl.dataset.nodeId = node.id;
    nodeEl.dataset.nodeType = node.type;
    
    // 节点内容
    const contentEl = document.createElement('div');
    contentEl.className = 'tree-node__content';
    
    // 展开/折叠按钮（如果有子节点）
    if (node.children && node.children.length > 0) {
      const toggleBtn = document.createElement('button');
      toggleBtn.className = 'tree-node__toggle';
      toggleBtn.innerHTML = '<svg width="12" height="12" viewBox="0 0 12 12"><path d="M4 2L8 6L4 10" stroke="currentColor" stroke-width="1.5" fill="none"/></svg>';
      toggleBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleNode(nodeEl);
      });
      contentEl.appendChild(toggleBtn);
    } else {
      const spacer = document.createElement('span');
      spacer.className = 'tree-node__spacer';
      contentEl.appendChild(spacer);
    }
    
    // 节点图标
    const iconEl = document.createElement('span');
    iconEl.className = `tree-node__icon tree-node__icon--${node.type}`;
    iconEl.textContent = getNodeIcon(node.type);
    contentEl.appendChild(iconEl);
    
    // 节点标题
    const titleEl = document.createElement('span');
    titleEl.className = 'tree-node__title';
    titleEl.textContent = node.title;
    contentEl.appendChild(titleEl);
    
    // 进度徽章
    if (node.type === 'project' || (node.children && node.children.length > 0)) {
      const badgeEl = createProgressBadge(node);
      contentEl.appendChild(badgeEl);
    }
    
    // 状态指示器
    const statusEl = document.createElement('span');
    statusEl.className = `tree-node__status tree-node__status--${node.status}`;
    statusEl.title = getStatusText(node.status);
    contentEl.appendChild(statusEl);
    
    // 点击事件
    contentEl.addEventListener('click', () => {
      selectNode(node);
    });
    
    nodeEl.appendChild(contentEl);
    
    // 子节点容器
    if (node.children && node.children.length > 0) {
      const childrenEl = document.createElement('div');
      childrenEl.className = 'tree-node__children';
      childrenEl.style.display = depth === 0 ? 'block' : 'none'; // 默认展开第一层
      
      node.children.forEach(child => {
        const childEl = createTreeNode(child, depth + 1);
        childrenEl.appendChild(childEl);
      });
      
      nodeEl.appendChild(childrenEl);
    }
    
    // 管理员操作按钮
    if (isAdminMode) {
      const actionsEl = createNodeActions(node);
      contentEl.appendChild(actionsEl);
    }
    
    return nodeEl;
  }

  /**
   * 切换节点展开/折叠
   */
  function toggleNode(nodeEl) {
    const childrenEl = nodeEl.querySelector('.tree-node__children');
    if (!childrenEl) return;
    
    const isExpanded = childrenEl.style.display !== 'none';
    childrenEl.style.display = isExpanded ? 'none' : 'block';
    
    const toggleBtn = nodeEl.querySelector('.tree-node__toggle');
    if (toggleBtn) {
      toggleBtn.classList.toggle('tree-node__toggle--expanded', !isExpanded);
    }
  }

  /**
   * 获取节点图标
   */
  function getNodeIcon(type) {
    const icons = {
      'root': '🌳',
      'area': '📚',
      'topic': '📖',
      'project': '🎯'
    };
    return icons[type] || '•';
  }

  /**
   * 获取状态文本
   */
  function getStatusText(status) {
    const texts = {
      'locked': '已锁定',
      'unlocked': '可学习',
      'completed': '已完成'
    };
    return texts[status] || '';
  }

  // ==================== ProgressBadge 组件 ====================

  /**
   * 创建进度徽章
   */
  function createProgressBadge(node) {
    const badgeEl = document.createElement('span');
    badgeEl.className = 'progress-badge';
    
    const progress = node.progress || 0;
    badgeEl.textContent = `${progress}%`;
    
    if (progress === 100) {
      badgeEl.classList.add('progress-badge--completed');
    } else if (progress > 0) {
      badgeEl.classList.add('progress-badge--in-progress');
    } else {
      badgeEl.classList.add('progress-badge--not-started');
    }
    
    return badgeEl;
  }

  // ==================== NodeDrawer 组件 ====================

  /**
   * 选择节点并显示详情
   */
  function selectNode(node) {
    selectedNode = node;
    
    // 高亮选中的节点
    qsa('.tree-node').forEach(el => {
      el.classList.remove('tree-node--selected');
    });
    const nodeEl = qs(`[data-node-id="${node.id}"]`);
    if (nodeEl) {
      nodeEl.classList.add('tree-node--selected');
    }
    
    // 显示节点详情抽屉
    showNodeDrawer(node);
  }

  /**
   * 显示节点详情抽屉
   */
  function showNodeDrawer(node) {
    const drawer = qs('#nodeDrawer');
    if (!drawer) return;
    
    drawer.classList.add('node-drawer--open');
    
    // 渲染节点详情
    renderNodeDetails(node);
  }

  /**
   * 渲染节点详情
   */
  function renderNodeDetails(node) {
    const drawer = qs('#nodeDrawer');
    if (!drawer) return;
    
    const titleEl = qs('#nodeDrawerTitle', drawer);
    const typeEl = qs('#nodeDrawerType', drawer);
    const descEl = qs('#nodeDrawerDesc', drawer);
    const hoursEl = qs('#nodeDrawerHours', drawer);
    const progressEl = qs('#nodeDrawerProgress', drawer);
    const statusEl = qs('#nodeDrawerStatus', drawer);
    const childrenEl = qs('#nodeDrawerChildren', drawer);
    const actionsEl = qs('#nodeDrawerActions', drawer);
    
    if (titleEl) titleEl.textContent = node.title;
    if (typeEl) typeEl.textContent = getTypeText(node.type);
    if (descEl) descEl.textContent = node.description || '暂无描述';
    if (hoursEl) hoursEl.textContent = `${node.estimatedHours || 0} 小时`;
    if (progressEl) {
      progressEl.textContent = `${node.progress || 0}%`;
      const progressBar = qs('.node-drawer__progress-bar', drawer);
      if (progressBar) {
        progressBar.style.width = `${node.progress || 0}%`;
      }
    }
    if (statusEl) {
      statusEl.textContent = getStatusText(node.status);
      statusEl.className = `node-drawer__status node-drawer__status--${node.status}`;
    }
    
    // 渲染子节点列表
    if (childrenEl && node.children && node.children.length > 0) {
      childrenEl.innerHTML = '';
      node.children.forEach(child => {
        const childEl = document.createElement('div');
        childEl.className = 'node-drawer__child-item';
        childEl.innerHTML = `
          <span class="node-drawer__child-icon">${getNodeIcon(child.type)}</span>
          <span class="node-drawer__child-title">${child.title}</span>
          <span class="node-drawer__child-progress">${child.progress || 0}%</span>
        `;
        childEl.addEventListener('click', () => selectNode(child));
        childrenEl.appendChild(childEl);
      });
    } else if (childrenEl) {
      childrenEl.innerHTML = '<div class="node-drawer__empty">无子节点</div>';
    }
    
    // 渲染操作按钮
    if (actionsEl) {
      actionsEl.innerHTML = '';
      
      if (node.type === 'project' && node.status !== 'locked') {
        if (node.status === 'completed') {
          const resetBtn = document.createElement('button');
          resetBtn.className = 'btn btn--ghost';
          resetBtn.textContent = '重置进度';
          resetBtn.addEventListener('click', () => {
            resetProject(node.id);
          });
          actionsEl.appendChild(resetBtn);
        } else {
          const completeBtn = document.createElement('button');
          completeBtn.className = 'btn btn--primary';
          completeBtn.textContent = '完成项目';
          completeBtn.addEventListener('click', () => {
            completeProject(node.id);
          });
          actionsEl.appendChild(completeBtn);
        }
      }
      
      if (isAdminMode) {
        const editBtn = document.createElement('button');
        editBtn.className = 'btn btn--ghost';
        editBtn.textContent = '编辑';
        editBtn.addEventListener('click', () => {
          showEditNodeModal(node);
        });
        actionsEl.appendChild(editBtn);
        
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'btn btn--ghost btn--danger';
        deleteBtn.textContent = '删除';
        deleteBtn.addEventListener('click', () => {
          if (confirm('确定要删除此节点吗？')) {
            deleteNode(node.id);
          }
        });
        actionsEl.appendChild(deleteBtn);
      }
    }
  }

  /**
   * 获取类型文本
   */
  function getTypeText(type) {
    const texts = {
      'root': '根节点',
      'area': '学习方向',
      'topic': '子方向',
      'project': '项目点'
    };
    return texts[type] || type;
  }

  /**
   * 关闭节点详情抽屉
   */
  function closeNodeDrawer() {
    const drawer = qs('#nodeDrawer');
    if (drawer) {
      drawer.classList.remove('node-drawer--open');
    }
    selectedNode = null;
  }

  // ==================== 项目操作 ====================

  /**
   * 完成项目
   */
  function completeProject(projectId) {
    if (KnowledgeTreeCore.completeProject(currentTree, projectId)) {
      // 重新渲染
      renderTreeView();
      renderProgressOverview();
      renderWeeklyTasks();
      
      // 更新详情抽屉
      if (selectedNode && selectedNode.id === projectId) {
        const updatedNode = KnowledgeTreeCore.findNodeById(currentTree, projectId);
        if (updatedNode) {
          renderNodeDetails(updatedNode);
          selectedNode = updatedNode;
        }
      }
      
      // 显示提示
      showNotification('项目已完成！', 'success');
    }
  }

  /**
   * 重置项目
   */
  function resetProject(projectId) {
    if (KnowledgeTreeCore.resetProject(currentTree, projectId)) {
      renderTreeView();
      renderProgressOverview();
      renderWeeklyTasks();
      
      if (selectedNode && selectedNode.id === projectId) {
        const updatedNode = KnowledgeTreeCore.findNodeById(currentTree, projectId);
        if (updatedNode) {
          renderNodeDetails(updatedNode);
          selectedNode = updatedNode;
        }
      }
      
      showNotification('项目已重置', 'info');
    }
  }

  // ==================== 进度概览 ====================

  /**
   * 渲染进度概览
   */
  function renderProgressOverview() {
    const container = qs('#progressOverview');
    if (!container) return;
    
    const totalProjects = KnowledgeTreeCore.getAllProjectNodes(currentTree).length;
    const completedProjects = KnowledgeTreeCore.getAllProjectNodes(currentTree)
      .filter(p => p.status === 'completed').length;
    const totalProgress = currentTree.progress || 0;
    const totalHours = KnowledgeTreeCore.calculateTotalHours(currentTree);
    const completedHours = calculateCompletedHours(currentTree);
    
    container.innerHTML = `
      <div class="progress-overview__item">
        <div class="progress-overview__label">总体进度</div>
        <div class="progress-overview__value">${totalProgress}%</div>
        <div class="progress-overview__bar">
          <div class="progress-overview__bar-fill" style="width: ${totalProgress}%"></div>
        </div>
      </div>
      <div class="progress-overview__item">
        <div class="progress-overview__label">已完成项目</div>
        <div class="progress-overview__value">${completedProjects} / ${totalProjects}</div>
      </div>
      <div class="progress-overview__item">
        <div class="progress-overview__label">学习时长</div>
        <div class="progress-overview__value">${completedHours} / ${totalHours} 小时</div>
      </div>
    `;
  }

  /**
   * 计算已完成的学习时长
   */
  function calculateCompletedHours(tree) {
    const projects = KnowledgeTreeCore.getAllProjectNodes(tree);
    return projects
      .filter(p => p.status === 'completed')
      .reduce((total, p) => total + (p.estimatedHours || 0), 0);
  }

  // ==================== 本周任务 ====================

  /**
   * 渲染本周任务
   */
  function renderWeeklyTasks() {
    const container = qs('#weeklyTasks');
    if (!container) return;
    
    const weekTasks = KnowledgeTreeCore.getCurrentWeekTasks(currentTree);
    
    if (!weekTasks || !weekTasks.projects || weekTasks.projects.length === 0) {
      container.innerHTML = '<div class="weekly-tasks__empty">本周暂无任务</div>';
      return;
    }
    
    container.innerHTML = `
      <div class="weekly-tasks__header">
        <h3 class="weekly-tasks__title">第 ${weekTasks.week} 周学习任务</h3>
        <div class="weekly-tasks__meta">
          ${weekTasks.totalHours} 小时 / ${Math.round(weekTasks.targetHours)} 小时
        </div>
      </div>
      <div class="weekly-tasks__list">
        ${weekTasks.projects.map(project => `
          <div class="weekly-tasks__item" data-project-id="${project.id}">
            <span class="weekly-tasks__icon">${getNodeIcon('project')}</span>
            <span class="weekly-tasks__name">${project.title}</span>
            <span class="weekly-tasks__hours">${project.estimatedHours || 0}h</span>
            ${project.status === 'completed' ? '<span class="weekly-tasks__check">✓</span>' : ''}
          </div>
        `).join('')}
      </div>
    `;
    
    // 绑定点击事件
    qsa('.weekly-tasks__item', container).forEach(item => {
      item.addEventListener('click', () => {
        const projectId = item.dataset.projectId;
        const project = KnowledgeTreeCore.findNodeById(currentTree, projectId);
        if (project) {
          selectNode(project);
        }
      });
    });
  }

  // ==================== 管理员功能 ====================

  /**
   * 创建节点操作按钮
   */
  function createNodeActions(node) {
    const actionsEl = document.createElement('div');
    actionsEl.className = 'tree-node__actions';
    
    const editBtn = document.createElement('button');
    editBtn.className = 'tree-node__action-btn';
    editBtn.textContent = '编辑';
    editBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      showEditNodeModal(node);
    });
    
    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'tree-node__action-btn tree-node__action-btn--danger';
    deleteBtn.textContent = '删除';
    deleteBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (confirm('确定要删除此节点吗？')) {
        deleteNode(node.id);
      }
    });
    
    actionsEl.appendChild(editBtn);
    actionsEl.appendChild(deleteBtn);
    
    return actionsEl;
  }

  /**
   * 显示编辑节点模态框
   */
  function showEditNodeModal(node) {
    // TODO: 实现编辑节点模态框
    alert('编辑功能开发中...');
  }

  /**
   * 删除节点
   */
  function deleteNode(nodeId) {
    // TODO: 实现删除节点逻辑
    alert('删除功能开发中...');
  }

  /**
   * 设置管理员模式
   */
  function setAdminMode(enabled) {
    isAdminMode = enabled;
    renderTreeView();
  }

  // ==================== 事件绑定 ====================

  /**
   * 绑定事件
   */
  function bindEvents() {
    // 关闭抽屉按钮
    const closeBtn = qs('#nodeDrawerClose');
    if (closeBtn) {
      closeBtn.addEventListener('click', closeNodeDrawer);
    }
    
    // 抽屉背景点击关闭
    const drawer = qs('#nodeDrawer');
    if (drawer) {
      drawer.addEventListener('click', (e) => {
        if (e.target === drawer) {
          closeNodeDrawer();
        }
      });
    }
    
    // 添加节点按钮（管理员）
    const addNodeBtn = qs('#addNodeBtn');
    if (addNodeBtn) {
      addNodeBtn.addEventListener('click', () => {
        showAddNodeModal();
      });
    }
  }

  /**
   * 显示添加节点模态框
   */
  function showAddNodeModal() {
    // TODO: 实现添加节点模态框
    alert('添加节点功能开发中...');
  }

  /**
   * 显示通知
   */
  function showNotification(message, type = 'info') {
    // 简单的通知实现
    const notification = document.createElement('div');
    notification.className = `notification notification--${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.classList.add('notification--show');
    }, 10);
    
    setTimeout(() => {
      notification.classList.remove('notification--show');
      setTimeout(() => {
        document.body.removeChild(notification);
      }, 300);
    }, 3000);
  }

  // ==================== 导出 ====================

  window.KnowledgeTreeUI = {
    init: initKnowledgeTreeUI,
    setAdminMode,
    refresh: () => {
      renderTreeView();
      renderProgressOverview();
      renderWeeklyTasks();
    }
  };

})();

