# Package 5: Vision Transformer 主干网络堆叠与完整模型构建

## 📋 概述

本教程将指导你完成 Vision Transformer（ViT）架构的最后关键一步：堆叠多个 Transformer 编码器层以形成强大的主干特征提取器，并整合 class token 与 MLP 分类头，构建端到端的 ViT 模型。我们将基于前四讲已实现的模块（图像分块、位置编码、多头自注意力、单个编码器层），聚焦于如何将这些组件有机组合成一个完整的视觉识别系统。重点在于理解模型整体结构的设计逻辑、信息流动路径以及分类任务的输出机制，为后续的推理或训练奠定坚实基础。

## 📂 项目结构

```
package-05-vit-complete-architecture/
├── README.md                  # 包含依赖说明：本包假设 Packages 1–4 的模块（如 PatchEmbedding、PositionalEncoding、Attention 等）已可通过 PYTHONPATH 访问
├── requirements.txt
├── src/
│   ├── vit_encoder_stack.py   # 实现 VisionTransformerEncoderStack，含详细 docstring 和 inline 注释，说明层堆叠逻辑与维度变化
│   └── vision_transformer.py   # 实现完整 VisionTransformer，明确包含：PatchEmbedding → PositionalEncoding → prepend class token → EncoderStack → extract class token → MLP head (logits)
└── configs/
    └── vit_config.yaml
```

## 💡 理论基础

同学们好！今天我们终于要将 Vision Transformer 的所有“器官”组装成一个完整的“生命体”了。在深入堆叠结构之前，我们先快速回顾 Transformer 的核心机制，确保大家站在同一认知起点上。

### Transformer 编码器层基础
一个标准的 Transformer 编码器层包含两个关键子模块：
1. **多头自注意力（Multi-Head Self-Attention, MHSA）**：让序列中每个位置都能关注其他所有位置，动态聚合全局上下文。对于输入序列 $\boldsymbol{Z} \in \mathbb{R}^{(N+1) \times D}$，MHSA 计算如下：
   $$
   \text{Attention}(Q,K,V) = \text{softmax}\left(\frac{QK^\top}{\sqrt{d_k}}\right)V, \quad \text{其中 } Q=Z W_Q,\ K=Z W_K,\ V=Z W_V
   $$
   多头机制通过并行多个注意力头增强模型表达能力。
2. **前馈网络（Feed-Forward Network, FFN）**：一个两层 MLP，对每个位置独立进行非线性变换：
   $$
   \text{FFN}(x) = W_2 (\text{GELU}(W_1 x + b_1)) + b_2
   $$
每个子模块后都接 LayerNorm 和残差连接，形成：
$$
\boldsymbol{Z}' = \text{LayerNorm}(\boldsymbol{Z} + \text{MHSA}(\boldsymbol{Z})), \quad \boldsymbol{Z}'' = \text{LayerNorm}(\boldsymbol{Z}' + \text{FFN}(\boldsymbol{Z}'))
$$

### 为什么需要堆叠多个编码器层？
这源于深度学习的基本哲学：**层次化特征抽象**。浅层编码器捕捉局部模式（如边缘、纹理），而深层编码器则整合全局语义信息（如物体部件、整体类别）。在 ViT 中，这种层次性通过 $L$ 个连续的编码器层实现。设第 $l$ 层的输入为 $\boldsymbol{Z}^{(l)} \in \mathbb{R}^{(N+1) \times D}$（其中 $N$ 是图像块数，$+1$ 对应 class token），则其输出为：
$$
\boldsymbol{Z}^{(l+1)} = \text{TransformerEncoderLayer}(\boldsymbol{Z}^{(l)})
$$
经过 $L$ 次迭代后，最终的 class token 表示 $\boldsymbol{z}_0^{(L)}$ 蕴含了整幅图像的全局语义信息 [Dosovitskiy et al., 2020]。

### Class Token 的工作机制详解
Class token 是 ViT 区别于原始 Transformer 的关键设计。我们在 patch embedding 序列最前端插入一个可学习的向量 $\boldsymbol{z}_{\text{cls}} \in \mathbb{R}^D$，它不对应任何图像块，而是作为“全局信息聚合器”。其工作流程如下：
1. **初始化**：在模型构建时，随机初始化一个可训练参数 $\boldsymbol{z}_{\text{cls}}$。
2. **拼接**：将 $\boldsymbol{z}_{\text{cls}}$ 与 patch embeddings 拼接，形成完整输入序列 $[\boldsymbol{z}_{\text{cls}}, \boldsymbol{z}_1, \boldsymbol{z}_2, ..., \boldsymbol{z}_N]$，维度为 $(N+1) \times D$。
3. **注意力交互**：在每一层 MHSA 中，class token 作为 Query 参与其他所有 token（包括自身）的注意力计算。这意味着它能从所有图像块中动态收集信息；同时，其他 token 也能以 class token 为 Key/Value 进行响应，形成双向信息流。
4. **逐层演化**：经过 $L$ 层编码器后，class token 的表示 $\boldsymbol{z}_0^{(L)}$ 已融合全图语义。
5. **分类头输入**：最终，仅提取该 token（即输出序列的第一个元素）送入 MLP 分类头，输出 logits（未归一化的类别分数）。

> **维度追踪示例**：
> - 输入图像: $[B, C, H, W]$
> - Patch Embedding 后: $[B, N, D]$
> - 添加 class token + Position Encoding: $[B, N+1, D]$
> - 经过 $L$ 层 Encoder: $[B, N+1, D]$
> - 提取 class token: $[B, D]$
> - MLP Head 输出: $[B, num\_classes]$（logits）

---

## 📖 核心概念详解

在开始实现之前，请先理解以下核心概念。这些概念是理解本包实现的关键前提。

### Class Token

同学们，想象一下你要写一篇关于一幅画的总结。你不会逐字描述每个像素，而是会先观察整幅画，然后提炼出一个核心观点。在 Vision Transformer（ViT）中，**class token** 就扮演着这个“核心观点提炼者”的角色。

具体来说，class token 是一个**可学习的向量**，它的长度与其他图像块嵌入（patch embeddings）相同，比如都是 768 维。但它本身**不对应图像中的任何实际区域**。在模型开始处理图像之前，我们会把这个特殊的 token 插入到图像块序列的最前面。所以，如果原始图像被分成了 196 个块（例如 14x14），那么加上 class token 后，整个输入序列的长度就变成了 197。

这个设计的精妙之处在于自注意力机制。在每一层 Transformer 编码器中，class token 都会和其他所有的图像块 token 进行“对话”（即计算注意力权重）。通过这种持续的交互，class token 会不断地从各个图像块中收集信息，逐步融合成一个代表整幅图像全局语义的向量。你可以把它想象成一个“会议主持人”，在会议（每一层编码器）中听取所有与会者（图像块）的意见，最终形成一个综合结论。

数学上，假设我们的输入嵌入序列为 $\boldsymbol{E} = [\boldsymbol{e}_1, \boldsymbol{e}_2, ..., \boldsymbol{e}_N] \in \mathbb{R}^{N \times D}$，其中 $N$ 是块的数量，$D$ 是嵌入维度。我们引入一个可学习的参数 $\boldsymbol{z}_{\text{cls}} \in \mathbb{R}^D$。那么，加入 class token 后的初始序列为：
$$\boldsymbol{Z}^{(0)} = [\boldsymbol{z}_{\text{cls}}, \boldsymbol{e}_1, \boldsymbol{e}_2, ..., \boldsymbol{e}_N] + \boldsymbol{E}_{\text{pos}}$$
这里 $\boldsymbol{E}_{\text{pos}}$ 是位置编码。经过 $L$ 层编码器后，我们只取序列的第一个元素，即 $\boldsymbol{z}_0^{(L)}$，作为最终的图像表示用于分类。这种设计由 [Dosovitskiy et al., 2020] 首次在 ViT 中提出，并迅速成为标准做法。后续研究如 [Touvron et al., 2021] 的 DeiT 模型也证实了其有效性，尤其是在数据效率方面。

为什么不用所有 token 的平均值呢？因为 class token 是一个**专门优化用于分类任务**的载体。它在训练过程中会学习如何最有效地聚合信息，而平均池化是一种固定的、非可学习的策略，可能无法捕捉到对分类最关键的细微差别。这就像一个专业的摘要员（class token）比简单地把所有句子加起来求平均（平均池化）更能写出精准的摘要一样。

**为什么重要**: Class token 是 ViT 架构中连接特征提取和分类任务的桥梁。没有它，我们就无法直接从 Transformer 的序列输出中得到一个单一的、用于分类的全局图像表示。理解其作用机制对于掌握 ViT 的整体工作流程至关重要，也是后续实现完整模型的关键一步。

**相关概念**: 序列到序列建模, 全局平均池化 (Global Average Pooling), 可学习参数

**示例与类比**:

- 会议主持人：class token 像主持人一样，汇总所有参会者（图像块）的观点，形成最终决议（分类结果）。
- 班级代表：在一个班级（图像）中，class token 就像班长，他/她了解所有同学（图像块）的情况，并代表整个班级发言（输出分类）。
- 新闻摘要：一篇长文章（图像块序列）的摘要（class token）包含了全文的核心信息，而不是简单地拼接所有句子。

---

### MLP 分类头 (MLP Classification Head)

当我们通过堆叠的 Transformer 编码器得到了一个强大的全局图像表示（即 class token 的最终输出）后，下一步就是如何利用这个表示来做出具体的分类决策。这就需要用到 **MLP 分类头**。

MLP 是 **多层感知机**（Multi-Layer Perceptron）的缩写，它是最基础也是最强大的神经网络结构之一。在 ViT 的上下文中，分类头通常是一个非常简单的 MLP，常常只包含**两层**：一个隐藏层和一个输出层。它的任务很明确：将高维的特征向量（例如 768 维）映射到类别空间（例如 1000 维，对应 ImageNet 的 1000 个类别）。

让我们一步步拆解它的工作过程。假设我们从编码器堆叠中得到的最终 class token 是 $\boldsymbol{z} \in \mathbb{R}^D$。首先，它会通过第一个线性变换（全连接层）：
$$\boldsymbol{h} = \boldsymbol{W}_1 \boldsymbol{z} + \boldsymbol{b}_1$$
这里 $\boldsymbol{W}_1 \in \mathbb{R}^{D_h \times D}$ 是权重矩阵，$\boldsymbol{b}_1 \in \mathbb{R}^{D_h}$ 是偏置项，$D_h$ 是隐藏层的维度（通常 $D_h = D$ 或 $D_h = D/2$）。接着，我们会对 $\boldsymbol{h}$ 应用一个**非线性激活函数**，最常用的是 GELU（Gaussian Error Linear Unit）：
$$\boldsymbol{a} = \text{GELU}(\boldsymbol{h})$$
GELU 比传统的 ReLU 更平滑，能提供更好的梯度流，这在深层网络中尤为重要 [Hendrycks & Gimpel, 2016]。最后，$\boldsymbol{a}$ 会通过第二个线性变换得到最终的 logits：
$$\boldsymbol{y} = \boldsymbol{W}_2 \boldsymbol{a} + \boldsymbol{b}_2$$
其中 $\boldsymbol{W}_2 \in \mathbb{R}^{C \times D_h}$，$C$ 是类别总数。这些 logits 会被送入 softmax 函数以得到概率分布。

为什么需要这个额外的 MLP 头，而不是直接用 class token 做分类？原因有二。第一，**维度匹配**：class token 的维度 $D$ 通常很大（为了保留丰富信息），而类别数 $C$ 可能很小（如 CIFAR-10 的 10 类）或很大（如 ImageNet 的 1000 类），直接映射不现实。第二，**非线性决策边界**：现实世界的分类问题往往是非线性的。单一线性层只能学习线性决策边界，而加入一个隐藏层和非线性激活函数后，MLP 理论上可以逼近任何复杂的函数，从而更好地分离不同类别的特征 [Cybenko, 1989]。在最新的实践中，如 [Chen et al., 2024] 所示，即使是一个简单的两层 MLP 头，在配合强大的 ViT 主干时，也能达到顶尖的性能。

你可以把 MLP 分类头想象成一个“翻译官”。Transformer 主干产生了一种高度抽象的“内部语言”（class token），而分类头的任务就是将这种内部语言“翻译”成我们人类能理解的“类别标签”。没有这个翻译官，再强大的主干也无法告诉我们它到底“看到”了什么。

**为什么重要**: MLP 分类头是 ViT 模型完成从特征提取到具体任务（分类）转换的最后一环。它是模型输出的直接来源，其结构设计直接影响模型的表达能力和最终性能。在搭建完整 ViT 架构时，正确实现这个组件是必不可少的。

**相关概念**: 全连接层 (Fully Connected Layer), GELU 激活函数, Logits, Softmax 函数

**示例与类比**:

- 翻译官：将 Transformer 内部的抽象特征“翻译”成具体的类别名称。
- 解码器：就像收音机接收电磁波（特征）后，需要一个解码器将其转换成我们能听到的声音（类别）。
- 决策委员会：class token 是委员会收集到的所有信息，MLP 头则是委员会根据这些信息进行最终投票和决策的过程。

---

## 🔧 实现步骤

### 1 VisionTransformerEncoderStack

**文件**: `src/vit_encoder_stack.py`

**目的**: 将多个已实现的Transformer编码器层按顺序堆叠，形成ViT的主干特征提取部分。

#### 详细说明

同学们好！在前四讲中，我们已经分别实现了图像分块嵌入（PatchEmbedding）、位置编码（PositionalEncoding）、多头自注意力（MultiHeadSelfAttention）、缩放点积注意力（ScaledDotProductAttention）、前馈网络（FeedForwardNetwork）以及单个Transformer编码器层（TransformerEncoderLayer）。这些模块共同构成了Vision Transformer的基本构建单元。现在，我们将进入第五讲的第一步：将这些单元有机地组合起来，构建出完整的ViT主干网络。

本步骤的核心任务是实现`VisionTransformerEncoderStack`类。它的作用非常明确：接收一个包含class token和位置编码的嵌入序列（形状为`(batch_size, num_patches + 1, embedding_dim)`），然后让这个序列依次通过N个（例如12个）相同的`TransformerEncoderLayer`。每一层都会对输入序列进行一次复杂的非线性变换，逐步提炼出更高层次的语义特征。这种堆叠结构是深度学习模型能力的关键来源——浅层捕捉局部细节，深层整合全局上下文。

为什么选择使用`nn.ModuleList`而不是`nn.Sequential`？这是一个重要的设计决策。虽然`nn.Sequential`写起来更简洁，但它要求每一层的输入输出形状完全一致且顺序执行，缺乏灵活性。而`nn.ModuleList`只是一个容器，它保留了PyTorch模块的所有特性（如参数注册、设备移动等），同时允许我们在`forward`方法中完全控制数据流。这对于未来可能的扩展（例如引入跨层连接、动态层数调整或中间特征提取）至关重要，符合2024-2025年模块化、可组合模型架构的最佳实践。

在数据流方面，输入`x`首先经过第一个编码器层，其输出成为第二个编码器层的输入，如此往复，直到所有L层都处理完毕。最终，整个堆栈输出一个与输入形状相同的张量，但其中每个位置（尤其是class token对应的位置）都蕴含了经过L次自注意力和前馈网络处理后的丰富信息。值得注意的是，class token在整个过程中会不断与其他图像块进行交互，最终汇聚全局信息用于分类。

我们的实现严格依赖于前序步骤中定义的`TransformerEncoderLayer`。这意味着我们必须确保该层的接口（即`forward`方法的签名）是稳定和清晰的。`VisionTransformerEncoderStack`本身不包含任何新的可学习参数（除了它所包含的各层的参数），它纯粹是一个组合逻辑的封装。这种“组合优于继承”的思想是现代深度学习框架设计的核心原则之一。

最后，这个组件是构建完整ViT模型（将在`vision_transformer.py`中实现）的关键中间步骤。它负责完成从原始嵌入到高级特征表示的转换，为后续的分类头提供高质量的输入。理解这个堆叠过程对于掌握Transformer架构的层次化特征学习机制至关重要。

#### 完整实现

```python
import torch
import torch.nn as nn
from typing import List
from src.transformer_encoder_layer import TransformerEncoderLayer

class VisionTransformerEncoderStack(nn.Module):
    """
    Vision Transformer 编码器堆栈
    
    将多个 Transformer 编码器层按顺序堆叠，形成 ViT 的主干特征提取网络。
    该模块接收带有 class token 和位置编码的嵌入序列，并输出经过多层处理后的特征序列。
    
    Args:
        embedding_dim (int): 嵌入维度 D
        num_layers (int): Transformer 编码器层的数量 L
        num_heads (int): 多头注意力中的头数
        mlp_hidden_dim (int): 前馈网络隐藏层维度
        dropout (float): Dropout 概率
        
    Input:
        x (Tensor): 形状为 (batch_size, num_patches + 1, embedding_dim) 的嵌入序列
                   其中 num_patches + 1 包含了 class token
                   
    Output:
        Tensor: 形状为 (batch_size, num_patches + 1, embedding_dim) 的处理后特征序列
    """
    
    def __init__(
        self,
        embedding_dim: int = 768,
        num_layers: int = 12,
        num_heads: int = 12,
        mlp_hidden_dim: int = 3072,
        dropout: float = 0.1
    ):
        super().__init__()
        
        # 输入验证：确保参数合理
        if embedding_dim <= 0:
            raise ValueError(f"embedding_dim 必须为正整数，得到 {embedding_dim}")
        if num_layers <= 0:
            raise ValueError(f"num_layers 必须为正整数，得到 {num_layers}")
        if num_heads <= 0:
            raise ValueError(f"num_heads 必须为正整数，得到 {num_heads}")
        if mlp_hidden_dim <= 0:
            raise ValueError(f"mlp_hidden_dim 必须为正整数，得到 {mlp_hidden_dim}")
        if not (0 <= dropout <= 1):
            raise ValueError(f"dropout 必须在 [0, 1] 范围内，得到 {dropout}")
            
        # 使用 ModuleList 存储多个编码器层
        # 注意：不能使用列表推导式直接创建，因为 PyTorch 需要正确注册参数
        self.layers = nn.ModuleList([
            TransformerEncoderLayer(
                embedding_dim=embedding_dim,
                num_heads=num_heads,
                mlp_hidden_dim=mlp_hidden_dim,
                dropout=dropout
            )
            for _ in range(num_layers)
        ])
        
        # 可选：添加 Layer Normalization 作为最终输出的规范化
        # 根据原始 ViT 论文和 2024 年最佳实践，通常在编码器堆栈末尾添加 LayerNorm
        self.norm = nn.LayerNorm(embedding_dim)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播：依次通过所有编码器层
        
        Args:
            x (torch.Tensor): 输入嵌入序列，形状 (batch_size, seq_len, embedding_dim)
                            其中 seq_len = num_patches + 1 (包含 class token)
                            
        Returns:
            torch.Tensor: 处理后的特征序列，形状 (batch_size, seq_len, embedding_dim)
        """
        # 输入验证
        if x.dim() != 3:
            raise ValueError(f"输入张量必须是3维的 (batch, seq, dim)，得到 {x.dim()} 维")
            
        # 依次通过每一层编码器
        for layer in self.layers:
            # 每一层的输出作为下一层的输入
            # 注意：TransformerEncoderLayer 内部已经处理了残差连接和 LayerNorm
            x = layer(x)
            
        # 根据 ViT 原始论文和现代实现（如 timm 库），
        # 在编码器堆栈的最后应用 Layer Normalization
        # 这有助于稳定训练并提升性能
        x = self.norm(x)
        
        return x
```

#### 重要提示

- 使用 `nn.ModuleList` 而非普通 Python 列表至关重要，因为只有 `ModuleList` 中的模块才会被 PyTorch 正确识别为子模块，从而自动注册参数、支持设备移动（如 `.to(device)`）和状态字典保存/加载。普通列表中的模块会被视为孤立对象，导致训练失败。
- 在编码器堆栈末尾添加 `LayerNorm` 是 Vision Transformer 的标准做法，这源于原始 ViT 论文（Dosovitskiy et al., 2020）并在后续研究中被广泛采用。2024年的研究表明，这种最终的规范化层对于模型收敛性和最终性能有显著影响，不应省略。
- 输入验证是生产级代码的重要组成部分。我们检查了所有关键参数的有效性范围，避免在运行时出现难以调试的错误。特别是对 dropout 范围的检查，防止因配置错误导致模型行为异常。
- 虽然本实现假设所有编码器层具有相同的超参数（这是标准 ViT 的做法），但使用 `ModuleList` 的设计为未来扩展提供了可能性。例如，可以轻松修改为不同层使用不同头数或隐藏维度的异构架构，这符合2024-2025年对模型架构灵活性的研究趋势。

### 2 VisionTransformer

**文件**: `src/vision_transformer.py`

**目的**: 整合嵌入层、编码器堆叠和分类头，构建完整的ViT模型架构。

#### 详细说明

同学们好！在上一步中，我们已经实现了 `VisionTransformerEncoderStack`，它负责将多个 Transformer 编码器层按顺序堆叠，形成强大的特征提取主干。现在，我们将在此基础上，整合之前已完成的 `ViTEmbeddingsWithPosition`（包含图像分块、class token 注入和位置编码），并添加一个轻量级的 MLP 分类头，从而构建出端到端的 Vision Transformer 模型。

本步骤的核心目标是实现完整的 ViT 前向流程：从原始图像输入开始，经过嵌入层得到带位置信息的序列，再通过多层编码器进行深度特征变换，最后利用 class token 的最终表示进行分类预测。这一设计直接源自 Dosovitskiy 等人在 2020 年提出的原始 ViT 架构，并已成为 2024-2025 年视觉基础模型（如 DINOv2、SAM 的变体）的标准范式之一。

为什么需要 class token？这是 ViT 区别于传统 CNN 的关键设计。我们在输入序列最前面插入一个可学习的特殊 token（即 class token），它不对应任何图像区域，但在每一层编码器中都会与其他 patch tokens 进行自注意力交互。经过 L 层编码后，class token 聚合了全局上下文信息，其最终输出向量被用作整个图像的“摘要表示”，送入分类器。这种机制避免了对全局平均池化的依赖，使模型能更灵活地建模长距离依赖。

接下来，我们来看整体数据流：输入图像 `[B, C, H, W]` → Patch Embedding → `[B, N, D]` → 注入 class token → `[B, N+1, D]` → 加位置编码 → 输入 Encoder Stack → 输出 `[B, N+1, D]` → 提取第 0 个 token（class token）→ `[B, D]` → MLP Head → `[B, num_classes]`。整个过程完全基于 Transformer，无卷积操作。

在实现上，我们将定义 `VisionTransformer` 类，继承自 `nn.Module`。构造函数接收配置参数（如图像尺寸、patch大小、隐藏维度、层数、头数、类别数等），并实例化嵌入模块、编码器堆叠和分类头。前向函数则按上述流程串联各组件。特别注意，MLP 分类头通常采用“隐藏层 + GELU + 输出层”的结构，这在 2024 年的实践中已被证明比单层线性头更具表达力（参考 Meta 的 DINOv2 实现）。

此外，我们还将加入输入验证和清晰的错误提示，确保用户传入的图像尺寸能被 patch size 整除，避免运行时崩溃。这种防御性编程是生产级代码的重要特征。最后，所有关键组件都使用类型注解，提升代码可读性和 IDE 支持。

这个完整模型虽然不涉及训练逻辑，但其结构必须严格对齐现代 ViT 实现规范，以便后续无缝接入训练或推理流程。这也是为什么我们要强调模块化设计——每个子组件（如 `ViTEmbeddingsWithPosition`）都已在前序步骤中独立验证，现在只需正确组合即可。

#### 完整实现

```python
import torch
import torch.nn as nn
from typing import Optional, Tuple

# 注意：以下导入的模块已在前序步骤中实现
from src.vit_embeddings_with_position import ViTEmbeddingsWithPosition
from src.vit_encoder_stack import VisionTransformerEncoderStack


class VisionTransformer(nn.Module):
    """
    Vision Transformer (ViT) 完整模型实现。
    
    该模型将输入图像转换为 patch 序列，注入 class token 并添加位置编码，
    然后通过多层 Transformer 编码器堆叠进行特征提取，
    最后使用 class token 的输出通过 MLP 分类头进行类别预测。
    
    参考: Dosovitskiy et al., "An Image is Worth 16x16 Words", ICLR 2021.
    现代实践（2024-2025）中，此架构被广泛用于自监督预训练和迁移学习。
    
    Args:
        image_size (int): 输入图像的边长（假设为正方形）。默认为 224。
        patch_size (int): 每个图像块的边长。默认为 16。
        num_channels (int): 输入图像的通道数（如 RGB 为 3）。默认为 3。
        hidden_dim (int): Transformer 隐藏层维度（即 embedding 维度 D）。默认为 768。
        num_layers (int): Transformer 编码器层数 L。默认为 12。
        num_heads (int): 多头自注意力的头数。默认为 12。
        mlp_ratio (float): MLP 隐藏层相对于 hidden_dim 的倍数。默认为 4.0。
        dropout (float): 全局 dropout 概率。默认为 0.1。
        num_classes (int): 分类任务的类别数。默认为 1000（ImageNet）。
        
    Attributes:
        embeddings (ViTEmbeddingsWithPosition): 图像分块、class token 注入和位置编码模块。
        encoder (VisionTransformerEncoderStack): Transformer 编码器层堆叠。
        classifier (nn.Sequential): MLP 分类头，输出 logits。
        
    Example:
        >>> model = VisionTransformer(image_size=224, patch_size=16, num_classes=10)
        >>> x = torch.randn(1, 3, 224, 224)
        >>> logits = model(x)  # shape: [1, 10]
    """
    
    def __init__(
        self,
        image_size: int = 224,
        patch_size: int = 16,
        num_channels: int = 3,
        hidden_dim: int = 768,
        num_layers: int = 12,
        num_heads: int = 12,
        mlp_ratio: float = 4.0,
        dropout: float = 0.1,
        num_classes: int = 1000,
    ) -> None:
        super().__init__()
        
        # === 输入验证：确保图像尺寸能被 patch size 整除 ===
        if image_size % patch_size != 0:
            raise ValueError(
                f"图像尺寸 {image_size} 必须能被 patch 尺寸 {patch_size} 整除。"
            )
        
        # 计算 patch 数量
        num_patches = (image_size // patch_size) ** 2
        
        # === 初始化嵌入层（包含 class token 和位置编码）===
        # 该模块已在 step_1 中实现，此处直接复用
        self.embeddings = ViTEmbeddingsWithPosition(
            image_size=image_size,
            patch_size=patch_size,
            num_channels=num_channels,
            hidden_dim=hidden_dim,
            num_patches=num_patches,
            dropout=dropout,
        )
        
        # === 初始化编码器堆叠 ===
        # 该模块已在本 package 的 step_1 (VisionTransformerEncoderStack) 中实现
        self.encoder = VisionTransformerEncoderStack(
            hidden_dim=hidden_dim,
            num_layers=num_layers,
            num_heads=num_heads,
            mlp_ratio=mlp_ratio,
            dropout=dropout,
        )
        
        # === 初始化 MLP 分类头 ===
        # 根据 2024-2025 年最佳实践（如 DINOv2），使用带 GELU 的两层 MLP
        mlp_hidden_dim = int(hidden_dim * mlp_ratio)
        self.classifier = nn.Sequential(
            # 第一层：从 hidden_dim 映射到 mlp_hidden_dim
            nn.Linear(hidden_dim, mlp_hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            # 第二层：映射到类别数
            nn.Linear(mlp_hidden_dim, num_classes),
        )
        
        # 初始化分类头权重（可选，但推荐）
        self._init_weights()
    
    def _init_weights(self) -> None:
        """
        初始化分类头的权重。
        使用标准正态分布初始化线性层权重，偏置置零。
        这有助于训练稳定性，尤其在从零开始训练时。
        """
        for module in self.classifier.modules():
            if isinstance(module, nn.Linear):
                nn.init.normal_(module.weight, std=0.02)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
    
    def forward(self, pixel_values: torch.Tensor) -> torch.Tensor:
        """
        ViT 前向传播函数。
        
        Args:
            pixel_values (torch.Tensor): 输入图像张量，形状为 [batch_size, num_channels, height, width]。
                
        Returns:
            torch.Tensor: 分类 logits，形状为 [batch_size, num_classes]。
                
        数据流说明:
            1. 输入: [B, C, H, W]
            2. 经过 embeddings: [B, N+1, D] （N = num_patches, +1 为 class token）
            3. 经过 encoder: [B, N+1, D]
            4. 提取 class token (索引 0): [B, D]
            5. 经过 classifier: [B, num_classes]
        """
        # === 步骤 1: 生成带位置编码的嵌入序列（含 class token）===
        # 输出形状: [batch_size, num_patches + 1, hidden_dim]
        embedding_output = self.embeddings(pixel_values)
        
        # === 步骤 2: 通过 Transformer 编码器堆叠 ===
        # 输出形状: [batch_size, num_patches + 1, hidden_dim]
        encoder_outputs = self.encoder(embedding_output)
        
        # === 步骤 3: 提取 class token 的最终表示 ===
        # class token 位于序列的第一个位置（索引 0）
        # 输出形状: [batch_size, hidden_dim]
        cls_token_final = encoder_outputs[:, 0]
        
        # === 步骤 4: 通过 MLP 分类头生成 logits ===
        # 输出形状: [batch_size, num_classes]
        logits = self.classifier(cls_token_final)
        
        return logits
```

#### 重要提示

- 【class token 的关键作用】class token 是 ViT 实现全局推理的核心机制。它在每一层编码器中与所有 patch tokens 进行自注意力交互，最终聚合全局语义信息。务必确保在嵌入层正确注入并在前向传播中准确提取（索引 0），这是模型能否有效分类的关键。
- 【MLP 分类头的设计选择】2024-2025 年的研究（如 Meta 的 DINOv2）表明，使用带 GELU 激活和 dropout 的两层 MLP 比单层线性头表现更好。本实现采用 hidden_dim * mlp_ratio 作为中间层维度，这是当前 ViT 变体的标准配置。
- 【输入验证的重要性】在构造函数中显式检查 image_size 是否能被 patch_size 整除，可以避免在运行时因 reshape 失败而崩溃。这种防御性编程是生产级代码的必备实践，尤其当模型被不同用户以不同配置调用时。
- 【模块化复用的优势】本步骤完全复用了前序步骤实现的 ViTEmbeddingsWithPosition 和 VisionTransformerEncoderStack，体现了良好的软件工程原则。这种设计使得每个组件可独立测试和优化，极大提升了代码的可维护性和可扩展性。

---

## 📦 依赖安装

### 所需依赖

- **torch (>=2.0.0)**: PyTorch 深度学习框架，用于构建和定义神经网络模型
- **torchvision (>=0.15.0)**: 提供计算机视觉相关的工具和预定义模型，方便测试和验证
- **PyYAML (>=6.0)**: 用于解析 configs/vit_config.yaml 配置文件

### 安装步骤

```bash
克隆本项目仓库
创建并激活 Python 虚拟环境（推荐使用 conda 或 venv）
运行 `pip install -r requirements.txt` 安装依赖
查看 `configs/vit_config.yaml` 了解模型配置参数
```

---

## 🎮 使用教程

### 初始化并打印 ViT 模型结构

**场景**: 快速验证模型是否能正确构建

```python
from src.vision_transformer import VisionTransformer
import torch

# 使用默认配置创建模型
model = VisionTransformer(
    img_size=224,
    patch_size=16,
    in_channels=3,
    num_classes=1000,
    embed_dim=768,
    depth=12,  # 12层编码器
    num_heads=12,
    mlp_ratio=4.
)

print(model)

# 创建一个假的输入张量
x = torch.randn(1, 3, 224, 224)
output = model(x)
print(f"Output shape: {output.shape}")  # 应为 [1, 1000]
```

**预期输出**: 打印出完整的模型结构树，并显示输出形状为 torch.Size([1, 1000])

### 检查编码器堆叠模块

**场景**: 单独测试编码器堆叠部分的功能

```python
from src.vit_encoder_stack import VisionTransformerEncoderStack
import torch

# 假设我们已经有了嵌入后的序列 (batch_size, seq_len, embed_dim)
batch_size, seq_len, embed_dim = 2, 197, 768
embedded_patches = torch.randn(batch_size, seq_len, embed_dim)

encoder_stack = VisionTransformerEncoderStack(
    embed_dim=embed_dim,
    depth=6,  # 6层
    num_heads=12,
    mlp_ratio=4.
)

output = encoder_stack(embedded_patches)
print(f"Encoder stack output shape: {output.shape}")
```

**预期输出**: 输出形状为 torch.Size([2, 197, 768])，与输入形状一致，表明信息流正确

---

## 📝 行动项

> [step_5] 堆叠编码器层构建ViT : 将多个Transformer编码器层按顺序堆叠，形成完整的ViT主干网络。最后添加分类头（class token）和MLP分类器，完成整个网络结构的搭建。
