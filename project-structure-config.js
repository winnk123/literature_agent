/**
 * 项目结构配置系统
 * 
 * 此配置定义了项目详情页的所有章节结构
 * 当队友更新此配置时，出题表单会自动同步更新
 * 
 * 配置版本：v1.0.0
 * 最后更新：2024年
 */

(function() {
  'use strict';
  
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
            { type: 'markdown', content: '# 背景\n\n在真实相机成像链路中，噪声来源包括读出噪声、光子噪声以及 ISP 处理引入的复合噪声。低照度、运动模糊与复杂背景进一步放大噪声影响，导致细节丢失与纹理伪影。' },
            { type: 'markdown', content: '## 数据来源\n\n- 合成数据集（DND、SIDD）\n- 真实数据集（自采样室内外场景）\n- 混合训练策略' },
            { type: 'code', content: '# 数据加载示例\nimport torch\nfrom torch.utils.data import Dataset\nimport numpy as np\nfrom PIL import Image\n\nprint("初始化数据加载器...")\nprint("DND数据集: 50张图像")\nprint("SIDD数据集: 320对图像")', language: 'python' },
            { type: 'markdown', content: '## 任务目标\n\n- 在保持结构一致性的前提下提升 PSNR/SSIM\n- 兼顾 LPIPS 感知质量\n- 实时推理速度 < 50ms' },
            { type: 'markdown', content: '## 难点分析\n\n- 弱光噪声分布不均\n- 跨设备域泛化能力\n- 速度与质量的平衡' }
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
            { type: 'markdown', content: '# 模型架构\n\n采用多尺度 U-Net 主干，结合噪声估计支路与频域残差补偿。整体结构为 Encoder-Decoder 框架，带跨层跳连与注意力模块。' },
            { type: 'code', content: '# 模型定义\nimport torch.nn as nn\n\nclass DenoiseModel(nn.Module):\n    def __init__(self, in_channels=3, base_dim=64):\n        super().__init__()\n        self.encoder = nn.Conv2d(in_channels, base_dim, 3, padding=1)\n        self.decoder = nn.Conv2d(base_dim, in_channels, 3, padding=1)', language: 'python' },
            { type: 'markdown', content: '## 核心模块\n\n模型包含以下关键组件：\n\n- 自适应门控注意力（AGA）模块\n- 频域残差增强（FRE）模块\n- 多尺度特征融合' },
            { type: 'code', content: '    def forward(self, x):\n        features = self.encoder(x)\n        output = self.decoder(features)\n        return output + x  # 残差连接\n\nmodel = DenoiseModel()\nprint(f"模型参数量: {sum(p.numel() for p in model.parameters())/1e6:.2f}M")', language: 'python' },
            { type: 'markdown', content: '训练阶段引入合成+真实的混合噪声建模与自蒸馏策略。' }
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
            { type: 'markdown', content: '# 一维卷积\n\n在介绍该模型之前，让我们先看看一维卷积是如何工作的。请记住，这只是基于互相关运算的二维卷积的特例。' },
            { type: 'table', content: {
              title: '下面展示了输入、核和输出的关系：',
              data: {
                input: [0, 1, 2, 3, 4, 5, 6],
                kernel: [1, 2],
                output: [2, 5, 8, 11, 14, 17],
                label: 'fig_conv1d'
              }
            }},
            { type: 'markdown', content: '如 :numref:`fig_conv1d` 中所示，在一维情况下，卷积窗口在输入张量上从左向右滑动。' },
            { type: 'code', content: 'def corr1d(X, K):\n    w = K.shape[0]\n    Y = torch.zeros((X.shape[0] - w + 1))\n    for i in range(Y.shape[0]):\n        Y[i] = (X[i: i + w] * K).sum()\n    return Y', language: 'python' }
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
            { type: 'markdown', content: '# Baseline介绍\n\n对比 BM3D、DnCNN、RIDNet、NAFNet 等。' }
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
            { type: 'markdown', content: '# IDEA引导\n\n本项目提供以下优化方向供探索。' },
            { type: 'markdown', content: '## 数据增强策略\n\n- 合成噪声混入相机 ISP 模拟过程\n- 多尺度裁剪与旋转增强\n- 混合噪声级别训练' },
            { type: 'code', content: '# 数据增强实现\nimport numpy as np\n\ndef add_realistic_noise(img, noise_level=0.1):\n    # 泊松噪声（光子噪声）\n    shot = np.random.poisson(img * 255) / 255.0\n    # 高斯噪声（读出噪声）\n    read = np.random.normal(0, noise_level, img.shape)\n    return np.clip(shot + read, 0, 1)', language: 'python' },
            { type: 'markdown', content: '## 结构优化方向\n\n- 探索轻量 Transformer 模块\n- 频域-空域双分支设计\n- 渐进式降噪策略' }
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
              question: "在图像去噪任务中，PSNR指标主要衡量什么？",
              options: ["图像的感知质量", "图像的峰值信噪比", "图像的结构相似度", "图像的颜色准确度"],
              correct: 1
            },
            {
              question: "ISP（Image Signal Processor）主要用于？",
              options: ["深度学习模型训练", "相机原始信号处理", "图像压缩", "视频编码"],
              correct: 1
            },
            {
              question: "DND数据集主要用于哪种任务？",
              options: ["图像分类", "图像去噪", "目标检测", "语义分割"],
              correct: 1
            },
            {
              question: "在深度学习中，Encoder-Decoder架构主要用于？",
              options: ["分类任务", "回归任务", "序列到序列任务", "聚类任务"],
              correct: 2
            },
            {
              question: "LPIPS指标主要衡量什么？",
              options: ["图像的峰值信噪比", "图像的感知相似度", "图像的结构相似度", "图像的均方误差"],
              correct: 1
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
    },
    
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
      console.log(`[ProjectStructureConfig] 执行配置迁移...`);
      // 处理版本迁移逻辑
    }
  };
  
  // 初始化时检查版本
  if (window.ProjectStructureConfig) {
    window.ProjectStructureConfig.checkVersion();
  }
  
  console.log('[ProjectStructureConfig] 配置系统已加载，版本:', window.ProjectStructureConfig.version);
})();

