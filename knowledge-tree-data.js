/**
 * 知识树数据模型和初始化数据
 * 定义知识树的数据结构，包含完整的AI学习路径
 */

// ==================== 数据模型定义 ====================

/**
 * 知识树节点类型
 * @typedef {'root' | 'area' | 'topic' | 'project'} NodeType
 */

/**
 * 节点状态
 * @typedef {'locked' | 'unlocked' | 'completed'} NodeStatus
 */

/**
 * 知识树节点数据结构
 * @typedef {Object} KnowledgeNode
 * @property {string} id - 唯一标识符
 * @property {string} title - 节点名称
 * @property {NodeType} type - 节点类型：root(根节点) | area(方向) | topic(子方向) | project(项目点)
 * @property {string} [description] - 节点描述
 * @property {KnowledgeNode[]} children - 子节点数组（无限层级递归）
 * @property {number} [estimatedHours] - 预计学习时长（小时）
 * @property {number} [progress] - 完成进度 0-100
 * @property {NodeStatus} status - 节点状态：locked(锁定) | unlocked(解锁) | completed(已完成)
 * @property {string} [parentId] - 父节点ID
 * @property {number} [order] - 排序序号
 * @property {string[]} [unlocks] - 完成此节点后解锁的节点ID列表
 * @property {string} [icon] - 图标（可选）
 */

// ==================== 初始化知识树数据 ====================

/**
 * 生成唯一ID
 */
function generateId(prefix = 'node') {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * 初始化知识树数据
 * 包含5个大方向，每个方向包含多个子方向和项目点
 */
const initialKnowledgeTree = {
  id: 'root-ai-learning',
  title: '人工智能（AI）学习总入口',
  type: 'root',
  description: 'AI领域全面入门学习路径，通过项目制学习掌握核心知识',
  children: [
    {
      id: 'area-math',
      title: '数学基础',
      type: 'area',
      description: 'AI学习所需的数学基础，包括线性代数、概率论、微积分等',
      estimatedHours: 80,
      status: 'unlocked',
      order: 1,
      children: [
        {
          id: 'topic-linear-algebra',
          title: '线性代数',
          type: 'topic',
          description: '矩阵运算、向量空间、特征值分解等',
          estimatedHours: 30,
          status: 'unlocked',
          order: 1,
          children: [
            {
              id: 'project-matrix-multiplication',
              title: '项目：矩阵乘法可视化',
              type: 'project',
              description: '实现矩阵乘法的可视化演示，理解矩阵运算的本质',
              estimatedHours: 4,
              status: 'unlocked',
              progress: 0,
              order: 1
            },
            {
              id: 'project-eigenvalue-calculator',
              title: '项目：特征值简单计算器',
              type: 'project',
              description: '编写程序计算矩阵的特征值和特征向量',
              estimatedHours: 5,
              status: 'locked',
              progress: 0,
              order: 2,
              unlocks: ['project-svd-decomposition']
            },
            {
              id: 'project-svd-decomposition',
              title: '项目：SVD分解实践',
              type: 'project',
              description: '实现奇异值分解（SVD）并应用于图像压缩',
              estimatedHours: 6,
              status: 'locked',
              progress: 0,
              order: 3
            }
          ]
        },
        {
          id: 'topic-probability-statistics',
          title: '概率论与统计',
          type: 'topic',
          description: '概率分布、统计推断、贝叶斯定理等',
          estimatedHours: 25,
          status: 'locked',
          order: 2,
          children: [
            {
              id: 'project-bayesian-inference',
              title: '项目：贝叶斯推理实践',
              type: 'project',
              description: '使用贝叶斯定理解决实际问题',
              estimatedHours: 6,
              status: 'locked',
              progress: 0,
              order: 1
            },
            {
              id: 'project-distribution-simulation',
              title: '项目：概率分布模拟',
              type: 'project',
              description: '模拟常见概率分布并可视化',
              estimatedHours: 5,
              status: 'locked',
              progress: 0,
              order: 2
            }
          ]
        },
        {
          id: 'topic-calculus',
          title: '微积分基础',
          type: 'topic',
          description: '导数、梯度、链式法则等',
          estimatedHours: 25,
          status: 'locked',
          order: 3,
          children: [
            {
              id: 'project-gradient-descent',
              title: '项目：梯度下降可视化',
              type: 'project',
              description: '实现并可视化梯度下降算法',
              estimatedHours: 6,
              status: 'locked',
              progress: 0,
              order: 1
            }
          ]
        }
      ]
    },
    {
      id: 'area-ml-basics',
      title: '机器学习基础',
      type: 'area',
      description: '监督学习、无监督学习、深度学习基础',
      estimatedHours: 120,
      status: 'locked',
      order: 2,
      unlocks: ['area-math'],
      children: [
        {
          id: 'topic-supervised-learning',
          title: '监督学习',
          type: 'topic',
          description: '分类、回归、决策树、SVM等',
          estimatedHours: 40,
          status: 'locked',
          order: 1,
          children: [
            {
              id: 'project-linear-regression',
              title: '项目：线性回归从零实现',
              type: 'project',
              description: '不使用库，从零实现线性回归算法',
              estimatedHours: 8,
              status: 'locked',
              progress: 0,
              order: 1
            },
            {
              id: 'project-decision-tree',
              title: '项目：决策树分类器',
              type: 'project',
              description: '实现决策树算法并应用于分类问题',
              estimatedHours: 10,
              status: 'locked',
              progress: 0,
              order: 2
            },
            {
              id: 'project-svm-classifier',
              title: '项目：SVM分类器',
              type: 'project',
              description: '实现支持向量机分类器',
              estimatedHours: 12,
              status: 'locked',
              progress: 0,
              order: 3
            }
          ]
        },
        {
          id: 'topic-unsupervised-learning',
          title: '无监督学习',
          type: 'topic',
          description: '聚类、降维、异常检测等',
          estimatedHours: 35,
          status: 'locked',
          order: 2,
          children: [
            {
              id: 'project-kmeans-clustering',
              title: '项目：K-Means聚类',
              type: 'project',
              description: '实现K-Means聚类算法',
              estimatedHours: 8,
              status: 'locked',
              progress: 0,
              order: 1
            },
            {
              id: 'project-pca-dimension-reduction',
              title: '项目：PCA降维实践',
              type: 'project',
              description: '使用主成分分析进行数据降维',
              estimatedHours: 10,
              status: 'locked',
              progress: 0,
              order: 2
            }
          ]
        },
        {
          id: 'topic-deep-learning-basics',
          title: '深度学习基础',
          type: 'topic',
          description: '神经网络、反向传播、正则化等',
          estimatedHours: 45,
          status: 'locked',
          order: 3,
          unlocks: ['topic-linear-algebra'],
          children: [
            {
              id: 'project-neural-network',
              title: '项目：神经网络从零实现',
              type: 'project',
              description: '不使用框架，从零实现多层神经网络',
              estimatedHours: 15,
              status: 'locked',
              progress: 0,
              order: 1
            },
            {
              id: 'project-backpropagation',
              title: '项目：反向传播算法',
              type: 'project',
              description: '实现并理解反向传播算法',
              estimatedHours: 12,
              status: 'locked',
              progress: 0,
              order: 2
            },
            {
              id: 'project-regularization',
              title: '项目：正则化技术',
              type: 'project',
              description: '实现Dropout、L2正则化等技术',
              estimatedHours: 10,
              status: 'locked',
              progress: 0,
              order: 3
            }
          ]
        }
      ]
    },
    {
      id: 'area-nlp',
      title: '自然语言处理（NLP）',
      type: 'area',
      description: '文本处理、词向量、Transformer、大语言模型',
      estimatedHours: 100,
      status: 'locked',
      order: 3,
      unlocks: ['area-ml-basics'],
      children: [
        {
          id: 'topic-text-processing',
          title: '文本处理基础',
          type: 'topic',
          description: '分词、词性标注、文本预处理',
          estimatedHours: 20,
          status: 'locked',
          order: 1,
          children: [
            {
              id: 'project-text-preprocessing',
              title: '项目：文本预处理工具',
              type: 'project',
              description: '实现文本清洗、分词、去停用词等功能',
              estimatedHours: 6,
              status: 'locked',
              progress: 0,
              order: 1
            }
          ]
        },
        {
          id: 'topic-word-embeddings',
          title: '词向量',
          type: 'topic',
          description: 'Word2Vec、GloVe、FastText等',
          estimatedHours: 25,
          status: 'locked',
          order: 2,
          children: [
            {
              id: 'project-word2vec',
              title: '项目：Word2Vec实现',
              type: 'project',
              description: '实现Word2Vec词向量训练',
              estimatedHours: 10,
              status: 'locked',
              progress: 0,
              order: 1
            }
          ]
        },
        {
          id: 'topic-transformer',
          title: 'Transformer架构',
          type: 'topic',
          description: '注意力机制、BERT、GPT等',
          estimatedHours: 35,
          status: 'locked',
          order: 3,
          unlocks: ['topic-deep-learning-basics'],
          children: [
            {
              id: 'project-attention-mechanism',
              title: '项目：注意力机制实现',
              type: 'project',
              description: '实现Transformer的注意力机制',
              estimatedHours: 12,
              status: 'locked',
              progress: 0,
              order: 1
            },
            {
              id: 'project-bert-finetune',
              title: '项目：BERT微调实践',
              type: 'project',
              description: '使用BERT进行文本分类任务',
              estimatedHours: 15,
              status: 'locked',
              progress: 0,
              order: 2
            }
          ]
        },
        {
          id: 'topic-llm',
          title: '大语言模型（LLM）',
          type: 'topic',
          description: 'GPT、ChatGPT、LLaMA等',
          estimatedHours: 20,
          status: 'locked',
          order: 4,
          unlocks: ['topic-transformer'],
          children: [
            {
              id: 'project-llm-finetune',
              title: '项目：LLM微调实践',
              type: 'project',
              description: '微调大语言模型完成特定任务',
              estimatedHours: 15,
              status: 'locked',
              progress: 0,
              order: 1
            }
          ]
        }
      ]
    },
    {
      id: 'area-mllm',
      title: '多模态大语言模型（MLLM）',
      type: 'area',
      description: '视觉-语言模型、多模态理解',
      estimatedHours: 80,
      status: 'locked',
      order: 4,
      unlocks: ['area-nlp'],
      children: [
        {
          id: 'topic-vision-language',
          title: '视觉-语言模型',
          type: 'topic',
          description: 'CLIP、BLIP、多模态融合',
          estimatedHours: 40,
          status: 'locked',
          order: 1,
          children: [
            {
              id: 'project-clip-implementation',
              title: '项目：CLIP模型实践',
              type: 'project',
              description: '使用CLIP进行图文匹配',
              estimatedHours: 12,
              status: 'locked',
              progress: 0,
              order: 1
            },
            {
              id: 'project-image-captioning',
              title: '项目：图像描述生成',
              type: 'project',
              description: '使用多模态模型生成图像描述',
              estimatedHours: 15,
              status: 'locked',
              progress: 0,
              order: 2
            }
          ]
        },
        {
          id: 'topic-multimodal-fusion',
          title: '多模态融合',
          type: 'topic',
          description: '跨模态理解、多模态预训练',
          estimatedHours: 40,
          status: 'locked',
          order: 2,
          children: [
            {
              id: 'project-multimodal-qa',
              title: '项目：多模态问答系统',
              type: 'project',
              description: '构建基于图像和文本的问答系统',
              estimatedHours: 18,
              status: 'locked',
              progress: 0,
              order: 1
            }
          ]
        }
      ]
    },
    {
      id: 'area-model-engineering',
      title: '模型工程',
      type: 'area',
      description: '模型部署、优化、分布式训练',
      estimatedHours: 90,
      status: 'locked',
      order: 5,
      unlocks: ['area-ml-basics'],
      children: [
        {
          id: 'topic-model-deployment',
          title: '模型部署',
          type: 'topic',
          description: '模型量化、推理优化、服务化',
          estimatedHours: 30,
          status: 'locked',
          order: 1,
          children: [
            {
              id: 'project-model-quantization',
              title: '项目：模型量化实践',
              type: 'project',
              description: '实现模型量化以减小模型大小',
              estimatedHours: 10,
              status: 'locked',
              progress: 0,
              order: 1
            },
            {
              id: 'project-model-serving',
              title: '项目：模型服务化部署',
              type: 'project',
              description: '使用Flask/FastAPI部署模型API',
              estimatedHours: 12,
              status: 'locked',
              progress: 0,
              order: 2
            }
          ]
        },
        {
          id: 'topic-distributed-training',
          title: '分布式训练',
          type: 'topic',
          description: '数据并行、模型并行、混合精度训练',
          estimatedHours: 35,
          status: 'locked',
          order: 2,
          children: [
            {
              id: 'project-ddp-training',
              title: '项目：分布式数据并行训练',
              type: 'project',
              description: '使用PyTorch DDP进行多GPU训练',
              estimatedHours: 15,
              status: 'locked',
              progress: 0,
              order: 1
            }
          ]
        },
        {
          id: 'topic-model-optimization',
          title: '模型优化',
          type: 'topic',
          description: '剪枝、蒸馏、架构搜索',
          estimatedHours: 25,
          status: 'locked',
          order: 3,
          children: [
            {
              id: 'project-model-pruning',
              title: '项目：模型剪枝实践',
              type: 'project',
              description: '实现模型剪枝以加速推理',
              estimatedHours: 12,
              status: 'locked',
              progress: 0,
              order: 1
            }
          ]
        }
      ]
    },
    {
      id: 'area-data-engineering',
      title: '数据工程',
      type: 'area',
      description: '数据采集、清洗、存储、处理',
      estimatedHours: 70,
      status: 'unlocked',
      order: 6,
      children: [
        {
          id: 'topic-data-collection',
          title: '数据采集',
          type: 'topic',
          description: '爬虫、API、数据标注',
          estimatedHours: 25,
          status: 'unlocked',
          order: 1,
          children: [
            {
              id: 'project-web-scraping',
              title: '项目：网页数据采集',
              type: 'project',
              description: '使用爬虫技术采集网页数据',
              estimatedHours: 8,
              status: 'unlocked',
              progress: 0,
              order: 1
            },
            {
              id: 'project-data-labeling',
              title: '项目：数据标注工具',
              type: 'project',
              description: '构建数据标注工具',
              estimatedHours: 10,
              status: 'locked',
              progress: 0,
              order: 2
            }
          ]
        },
        {
          id: 'topic-data-processing',
          title: '数据处理',
          type: 'topic',
          description: 'ETL、数据清洗、特征工程',
          estimatedHours: 25,
          status: 'locked',
          order: 2,
          children: [
            {
              id: 'project-etl-pipeline',
              title: '项目：ETL数据处理管道',
              type: 'project',
              description: '构建完整的数据ETL管道',
              estimatedHours: 12,
              status: 'locked',
              progress: 0,
              order: 1
            }
          ]
        },
        {
          id: 'topic-data-storage',
          title: '数据存储',
          type: 'topic',
          description: '数据库、数据仓库、向量数据库',
          estimatedHours: 20,
          status: 'locked',
          order: 3,
          children: [
            {
              id: 'project-vector-db',
              title: '项目：向量数据库实践',
              type: 'project',
              description: '使用向量数据库存储和检索嵌入向量',
              estimatedHours: 10,
              status: 'locked',
              progress: 0,
              order: 1
            }
          ]
        }
      ]
    }
  ],
  status: 'unlocked',
  progress: 0,
  estimatedHours: 540
};

// ==================== 工具函数 ====================

/**
 * 计算节点的总预计时长（递归计算所有子节点）
 */
function calculateTotalHours(node) {
  if (!node.children || node.children.length === 0) {
    return node.estimatedHours || 0;
  }
  return node.children.reduce((total, child) => total + calculateTotalHours(child), 0);
}

/**
 * 计算节点的完成进度（递归计算）
 */
function calculateProgress(node) {
  if (!node.children || node.children.length === 0) {
    return node.progress || 0;
  }
  
  const childrenProgress = node.children.map(child => calculateProgress(child));
  const totalProgress = childrenProgress.reduce((sum, p) => sum + p, 0);
  return Math.round(totalProgress / childrenProgress.length);
}

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
 * 获取所有项目节点（叶子节点）
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
 * 获取节点的所有祖先节点
 */
function getAncestors(tree, nodeId) {
  const ancestors = [];
  function traverse(node, path) {
    if (node.id === nodeId) {
      return path;
    }
    if (node.children) {
      for (const child of node.children) {
        const result = traverse(child, [...path, node]);
        if (result) return result;
      }
    }
    return null;
  }
  return traverse(tree, []) || [];
}

/**
 * 初始化知识树（设置parentId和order）
 */
function initializeTree(tree, parentId = null, order = 0) {
  tree.parentId = parentId;
  tree.order = order;
  if (tree.children) {
    tree.children.forEach((child, index) => {
      initializeTree(child, tree.id, index);
    });
  }
  return tree;
}

// 初始化知识树
const knowledgeTree = initializeTree(JSON.parse(JSON.stringify(initialKnowledgeTree)));

// 导出到全局（供其他脚本使用）
window.knowledgeTree = knowledgeTree;
window.initialKnowledgeTree = initialKnowledgeTree;

// 导出
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    knowledgeTree,
    initialKnowledgeTree,
    generateId,
    calculateTotalHours,
    calculateProgress,
    findNodeById,
    getAllProjectNodes,
    getAncestors,
    initializeTree
  };
}

