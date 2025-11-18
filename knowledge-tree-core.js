/**
 * 知识树核心逻辑模块
 * 包含点亮逻辑、进度更新、路线图生成、解锁逻辑等
 */

(function() {
  'use strict';

  // ==================== 数据管理 ====================

  /**
   * 从localStorage加载知识树数据
   */
  function loadKnowledgeTree() {
    try {
      const stored = localStorage.getItem('knowledgeTree');
      if (stored) {
        return JSON.parse(stored);
      }
    } catch (e) {
      console.warn('加载知识树数据失败，使用默认数据', e);
    }
    // 如果没有存储的数据，使用初始数据
    if (typeof knowledgeTree !== 'undefined') {
      return JSON.parse(JSON.stringify(knowledgeTree));
    }
    return null;
  }

  /**
   * 保存知识树数据到localStorage
   */
  function saveKnowledgeTree(tree) {
    try {
      localStorage.setItem('knowledgeTree', JSON.stringify(tree));
      return true;
    } catch (e) {
      console.error('保存知识树数据失败', e);
      return false;
    }
  }

  /**
   * 从localStorage加载用户进度
   */
  function loadUserProgress() {
    try {
      const stored = localStorage.getItem('knowledgeTreeProgress');
      if (stored) {
        return JSON.parse(stored);
      }
    } catch (e) {
      console.warn('加载用户进度失败', e);
    }
    return {};
  }

  /**
   * 保存用户进度到localStorage
   */
  function saveUserProgress(progress) {
    try {
      localStorage.setItem('knowledgeTreeProgress', JSON.stringify(progress));
      return true;
    } catch (e) {
      console.error('保存用户进度失败', e);
      return false;
    }
  }

  // ==================== 进度计算 ====================

  /**
   * 计算节点的完成进度（递归）
   */
  function calculateNodeProgress(node) {
    if (!node.children || node.children.length === 0) {
      // 叶子节点，直接返回自己的进度
      return node.progress || 0;
    }
    
    // 非叶子节点，计算子节点的平均进度
    const childrenProgress = node.children.map(child => calculateNodeProgress(child));
    if (childrenProgress.length === 0) return 0;
    
    const totalProgress = childrenProgress.reduce((sum, p) => sum + p, 0);
    const avgProgress = Math.round(totalProgress / childrenProgress.length);
    
    // 更新节点进度
    node.progress = avgProgress;
    
    return avgProgress;
  }

  /**
   * 更新节点状态（基于进度）
   */
  function updateNodeStatus(node) {
    if (node.type === 'project') {
      // 项目节点：progress = 100 时完成
      if (node.progress >= 100) {
        node.status = 'completed';
      } else if (node.status === 'locked') {
        // 保持锁定状态，除非被解锁
      } else {
        node.status = 'unlocked';
      }
    } else {
      // 非项目节点：根据子节点状态更新
      if (!node.children || node.children.length === 0) {
        return;
      }
      
      const allCompleted = node.children.every(child => child.status === 'completed');
      const someUnlocked = node.children.some(child => child.status === 'unlocked' || child.status === 'completed');
      
      if (allCompleted) {
        node.status = 'completed';
      } else if (someUnlocked) {
        node.status = 'unlocked';
      }
    }
  }

  /**
   * 递归更新整棵树的状态和进度
   */
  function updateTreeStatus(tree) {
    if (!tree) return;
    
    // 先更新子节点
    if (tree.children) {
      tree.children.forEach(child => updateTreeStatus(child));
    }
    
    // 计算进度
    calculateNodeProgress(tree);
    
    // 更新状态
    updateNodeStatus(tree);
  }

  // ==================== 点亮逻辑 ====================

  /**
   * 点亮项目节点（标记为完成）
   */
  function completeProject(tree, projectId) {
    function findAndComplete(node) {
      if (node.id === projectId) {
        if (node.type === 'project') {
          node.progress = 100;
          node.status = 'completed';
          
          // 解锁后续节点
          if (node.unlocks && node.unlocks.length > 0) {
            node.unlocks.forEach(unlockId => {
              const unlockNode = findNodeById(tree, unlockId);
              if (unlockNode && unlockNode.status === 'locked') {
                unlockNode.status = 'unlocked';
              }
            });
          }
          
          return true;
        }
        return false;
      }
      
      if (node.children) {
        for (const child of node.children) {
          if (findAndComplete(child)) {
            return true;
          }
        }
      }
      return false;
    }
    
    const found = findAndComplete(tree);
    if (found) {
      // 更新整棵树的状态和进度
      updateTreeStatus(tree);
      // 保存到localStorage
      saveKnowledgeTree(tree);
      return true;
    }
    return false;
  }

  /**
   * 取消完成项目（重置进度）
   */
  function resetProject(tree, projectId) {
    function findAndReset(node) {
      if (node.id === projectId) {
        if (node.type === 'project') {
          node.progress = 0;
          node.status = 'unlocked';
          return true;
        }
        return false;
      }
      
      if (node.children) {
        for (const child of node.children) {
          if (findAndReset(child)) {
            return true;
          }
        }
      }
      return false;
    }
    
    const found = findAndReset(tree);
    if (found) {
      updateTreeStatus(tree);
      saveKnowledgeTree(tree);
      return true;
    }
    return false;
  }

  // ==================== 解锁逻辑 ====================

  /**
   * 根据前置条件解锁节点
   */
  function unlockNodesByPrerequisites(tree) {
    function checkPrerequisites(node) {
      // 如果节点已解锁或已完成，跳过
      if (node.status !== 'locked') {
        return;
      }
      
      // 检查unlocks字段中的前置节点
      if (node.unlocks && node.unlocks.length > 0) {
        const allPrerequisitesMet = node.unlocks.every(prereqId => {
          const prereqNode = findNodeById(tree, prereqId);
          return prereqNode && prereqNode.status === 'completed';
        });
        
        if (allPrerequisitesMet) {
          node.status = 'unlocked';
        }
      }
      
      // 递归检查子节点
      if (node.children) {
        node.children.forEach(checkPrerequisites);
      }
    }
    
    checkPrerequisites(tree);
  }

  // ==================== 路线图生成 ====================

  /**
   * 生成一年学习路线图
   */
  function generateYearlyRoadmap(tree) {
    const totalHours = calculateTotalHours(tree);
    const daysInYear = 365;
    const hoursPerDay = totalHours / daysInYear; // 平均每天学习时长
    
    // 获取所有项目节点
    const projects = getAllProjectNodes(tree);
    
    // 按estimatedHours排序（从小到大）
    const sortedProjects = projects
      .filter(p => p.status !== 'completed')
      .sort((a, b) => (a.estimatedHours || 0) - (b.estimatedHours || 0));
    
    // 生成每周计划
    const weeklyPlans = [];
    let currentWeek = 1;
    let currentWeekHours = 0;
    const targetWeeklyHours = hoursPerDay * 7;
    
    const currentWeekProjects = [];
    
    for (const project of sortedProjects) {
      const projectHours = project.estimatedHours || 0;
      
      if (currentWeekHours + projectHours <= targetWeeklyHours) {
        currentWeekProjects.push(project);
        currentWeekHours += projectHours;
      } else {
        // 当前周已满，开始新的一周
        if (currentWeekProjects.length > 0) {
          weeklyPlans.push({
            week: currentWeek,
            projects: [...currentWeekProjects],
            totalHours: currentWeekHours,
            targetHours: targetWeeklyHours
          });
        }
        currentWeek++;
        currentWeekProjects.length = 0;
        currentWeekProjects.push(project);
        currentWeekHours = projectHours;
      }
    }
    
    // 添加最后一周
    if (currentWeekProjects.length > 0) {
      weeklyPlans.push({
        week: currentWeek,
        projects: [...currentWeekProjects],
        totalHours: currentWeekHours,
        targetHours: targetWeeklyHours
      });
    }
    
    return {
      totalHours,
      daysInYear,
      hoursPerDay: Math.round(hoursPerDay * 10) / 10,
      weeklyPlans,
      totalWeeks: weeklyPlans.length
    };
  }

  /**
   * 获取本周学习任务
   */
  function getCurrentWeekTasks(tree) {
    const roadmap = generateYearlyRoadmap(tree);
    if (roadmap.weeklyPlans.length === 0) {
      return null;
    }
    
    // 计算当前是第几周（从系统开始时间或用户设置的时间开始）
    const startDate = getStartDate();
    const now = new Date();
    const weeksSinceStart = Math.floor((now - startDate) / (7 * 24 * 60 * 60 * 1000));
    const currentWeekIndex = Math.min(weeksSinceStart, roadmap.weeklyPlans.length - 1);
    
    return roadmap.weeklyPlans[currentWeekIndex] || roadmap.weeklyPlans[0];
  }

  /**
   * 获取学习开始日期（从localStorage或使用当前日期）
   */
  function getStartDate() {
    try {
      const stored = localStorage.getItem('knowledgeTreeStartDate');
      if (stored) {
        return new Date(stored);
      }
    } catch (e) {
      console.warn('获取开始日期失败', e);
    }
    
    // 如果没有设置，使用当前日期
    const now = new Date();
    localStorage.setItem('knowledgeTreeStartDate', now.toISOString());
    return now;
  }

  /**
   * 设置学习开始日期
   */
  function setStartDate(date) {
    try {
      localStorage.setItem('knowledgeTreeStartDate', date.toISOString());
      return true;
    } catch (e) {
      console.error('设置开始日期失败', e);
      return false;
    }
  }

  // ==================== 工具函数 ====================

  /**
   * 查找节点（通过ID）
   */
  function findNodeById(tree, nodeId) {
    if (tree.id === nodeId) {
      return tree;
    }
    if (tree.children) {
      for (const child of tree.children) {
        const found = findNodeById(child, nodeId);
        if (found) return found;
      }
    }
    return null;
  }

  /**
   * 获取所有项目节点
   */
  function getAllProjectNodes(tree) {
    const projects = [];
    function traverse(node) {
      if (node.type === 'project') {
        projects.push(node);
      }
      if (node.children) {
        node.children.forEach(traverse);
      }
    }
    traverse(tree);
    return projects;
  }

  /**
   * 计算节点总时长（递归）
   */
  function calculateTotalHours(node) {
    if (!node.children || node.children.length === 0) {
      return node.estimatedHours || 0;
    }
    return node.children.reduce((total, child) => total + calculateTotalHours(child), 0);
  }

  /**
   * 获取节点的完整路径（从根节点到当前节点）
   */
  function getNodePath(tree, nodeId) {
    const path = [];
    function traverse(node, currentPath) {
      const newPath = [...currentPath, node];
      if (node.id === nodeId) {
        path.push(...newPath);
        return true;
      }
      if (node.children) {
        for (const child of node.children) {
          if (traverse(child, newPath)) {
            return true;
          }
        }
      }
      return false;
    }
    traverse(tree, []);
    return path;
  }

  // ==================== 导出 ====================

  window.KnowledgeTreeCore = {
    // 数据管理
    loadKnowledgeTree,
    saveKnowledgeTree,
    loadUserProgress,
    saveUserProgress,
    
    // 进度计算
    calculateNodeProgress,
    updateNodeStatus,
    updateTreeStatus,
    
    // 点亮逻辑
    completeProject,
    resetProject,
    
    // 解锁逻辑
    unlockNodesByPrerequisites,
    
    // 路线图生成
    generateYearlyRoadmap,
    getCurrentWeekTasks,
    getStartDate,
    setStartDate,
    
    // 工具函数
    findNodeById,
    getAllProjectNodes,
    calculateTotalHours,
    getNodePath
  };

})();

