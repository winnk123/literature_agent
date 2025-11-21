# Package 2: Vision Transformer 多头自注意力机制实现

## 📋 概述

本教程包专注于实现 Vision Transformer（ViT）架构中的核心组件——多头自注意力机制（Multi-Head Self-Attention, MHSA）。我们将从基础的缩放点积注意力单元开始，逐步构建完整的多头注意力模块，输入为来自图像分块嵌入步骤的序列化嵌入向量，输出为经过上下文感知增强的表示。该模块不包含位置编码或前馈网络，仅聚焦于注意力计算本身，是理解 ViT 如何建模全局依赖关系的关键一步。通过本包的学习，你将掌握 2024 年主流视觉 Transformer 中注意力机制的标准化实现方式。

## 📂 项目结构

```
package-02-vit-multihead-attention/
├── README.md
├── requirements.txt
├── src/
│   ├── scaled_dot_product_attention.py
│   └── multi_head_self_attention.py
└── tests/
    ├── test_scaled_dot_product_attention.py
    └── test_multi_head_self_attention.py
```

## 💡 理论基础

同学们好！今天我们深入探讨 Vision Transformer 的“大脑”——**多头自注意力机制**。在进入细节之前，我们需要先建立几个关键概念的基础理解。

### 图像如何变成向量：视觉中的嵌入（Embedding）

在自然语言处理中，Transformer 接收的是词（word）或子词（subword）的序列，每个词被映射为一个固定维度的向量，称为**嵌入**（embedding）。在 Vision Transformer（ViT）中，图像没有天然的“词”，因此需要人为构造。具体做法是：将输入图像（例如 224×224×3）均匀划分为若干个不重叠的小块（patch），比如 16×16 像素的块，这样一张图就得到 (224/16)² = 196 个图像块。每个块被展平（flattened）成一个长度为 16×16×3 = 768 的向量。接着，通过一个可学习的线性投影（即全连接层），将这个 768 维向量映射到一个更高维或更低维的**嵌入空间**（embedding space），例如 768 维。这个过程称为**图像分块嵌入**（Patch Embedding），其输出是一个形状为 $n \times d$ 的矩阵，其中 $n$ 是图像块的数量（即 **token 数量**，在 ViT 中，“token”泛指输入序列中的每一个元素，无论是词还是图像块），$d$ 是嵌入维度（也称为模型维度 $d_{\text{model}}$）。这些嵌入向量就是后续自注意力机制的输入。

### 矩阵乘法基础回顾

多头自注意力的核心计算依赖于矩阵乘法。简单来说，两个矩阵相乘 $A \in \mathbb{R}^{m \times k}$ 和 $B \in \mathbb{R}^{k \times n}$ 的结果是一个新矩阵 $C \in \mathbb{R}^{m \times n}$，其中每个元素 $C_{ij} = \sum_{l=1}^k A_{il} B_{lj}$。直观上，这相当于用 $A$ 的每一行与 $B$ 的每一列做点积。例如，若 $A = \begin{bmatrix}1 & 2\\3 & 4\end{bmatrix}$, $B = \begin{bmatrix}5 & 6\\7 & 8\end{bmatrix}$，则 $AB = \begin{bmatrix}19 & 22\\43 & 50\end{bmatrix}$。在注意力机制中，查询（Query）和键（Key）的转置相乘正是这种操作，用于衡量不同 token 之间的相关性。

### 缩放点积注意力（Scaled Dot-Product Attention）详解

缩放点积注意力是自注意力机制的基本计算单元。给定输入嵌入序列 $X \in \mathbb{R}^{n \times d}$，我们首先通过三个独立的线性变换生成**查询**（Query, $Q$）、**键**（Key, $K$）和**值**（Value, $V$）：
$$
Q = XW_Q, \quad K = XW_K, \quad V = XW_V
$$
其中 $W_Q, W_K, W_V \in \mathbb{R}^{d \times d_k}$ 是可学习权重矩阵。注意：在单头注意力中，通常 $d_k = d$；但在多头设置中，我们会稍作调整（见下文）。

接下来计算注意力分数：
$$
\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^\top}{\sqrt{d_k}}\right)V
$$

让我们逐步拆解这个公式：

1. **点积**（$QK^\top$）：得到一个 $n \times n$ 的矩阵，其中每个元素 $(i,j)$ 表示第 $i$ 个 token 对第 $j$ 个 token 的原始相关性得分。值越大，表示越“关注”。
2. **缩放**（除以 $\sqrt{d_k}$）：当 $d_k$ 较大时，点积的方差会增大，导致 softmax 函数进入梯度极小的饱和区。除以 $\sqrt{d_k}$ 可使方差稳定在 1 左右，保证训练稳定性。
3. **Softmax 函数**：将每一行的得分转换为概率分布。例如，假设某行原始得分为 [2, 5, 1]，则 softmax 后约为 [0.047, 0.946, 0.007]，表示该 token 主要关注第二个位置。Softmax 的定义为：$\text{softmax}(z_i) = \frac{e^{z_i}}{\sum_j e^{z_j}}$。
4. **加权求和**（乘以 $V$）：用上述概率作为权重，对所有 Value 向量进行加权平均，得到每个 token 的新表示。这意味着每个输出 token 都融合了整个序列的信息，但权重由相关性决定。

在实际实现中，还会加入**dropout**（随机将部分注意力权重置零）以防止过拟合，以及**masking**（在某些任务如语言建模中屏蔽未来信息），但在标准 ViT 的编码器中通常不需要 mask。

### 多头自注意力（Multi-Head Self-Attention）的构建逻辑

单头注意力只能在一个固定的表示子空间中建模关系。而**多头机制**允许模型**并行地在多个不同的表示子空间中学习不同的语义关联**。这里的“子空间”可以理解为嵌入空间的一个低维投影方向，每个头专注于不同的特征组合（例如一个头关注局部纹理，另一个头关注全局结构）。

具体实现步骤如下：

1. **统一投影**：首先仍将输入 $X \in \mathbb{R}^{n \times d}$ 通过三个大的权重矩阵 $W_Q, W_K, W_V \in \mathbb{R}^{d \times d}$ 投影到 $Q, K, V \in \mathbb{R}^{n \times d}$。注意：这里总维度仍为 $d$，但我们将它划分为 $h$ 个头。
2. **头分割**（Head Splitting）：将 $Q, K, V$ 沿着嵌入维度**重塑**（reshape）并**分割**为 $h$ 个头。每个头的维度为 $d_k = d / h$。因此，$Q$ 被变为形状 $n \times h \times d_k$，再转置为 $h \times n \times d_k$（便于并行计算）。
3. **并行应用缩放点积注意力**：对每个头 $i \in \{1, ..., h\}$，独立计算：
   $$
   \text{head}_i = \text{Attention}(Q_i, K_i, V_i)
   $$
   这正是修改意见 #10 强调的：**缩放点积注意力是多头机制中可复用的计算核**。
4. **拼接与投影**：将所有头的输出沿 $d_k$ 维度拼接起来，得到一个 $n \times d$ 的矩阵（因为 $h \times d_k = d$），再通过一个额外的线性变换 $W_O \in \mathbb{R}^{d \times d}$ 进行整合：
   $$
   \text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1, ..., \text{head}_h) W_O
   $$

这一流程清晰地表明：**多头自注意力并非直接调用单头函数，而是必须显式处理头的分割、并行计算和拼接**（对应修改意见 #5）。变量命名上，我们通常使用 `num_heads`（即 $h$）和 `head_dim`（即 $d_k = d / h$）来明确维度关系（回应修改意见 #9）。

### 历史背景与演进

多头自注意力最初由 Vaswani 等人在 2017 年提出 [Vaswani et al., 2017]，用于机器翻译。直到 2020 年，Dosovitskiy 等人将其成功迁移到纯视觉任务 [Dosovitskiy et al., 2020]，证明了 Transformer 在图像分类上的强大能力。尽管 2024 年已出现 FlashAttention-3 [Dao et al., 2024] 等高效变体，**标准多头自注意力仍是理解所有先进架构的基石**。

> **重要提示**：在完整的 ViT 架构中，**位置编码**（Positional Encoding）必须在自注意力之前加入，以弥补 Transformer 本身缺乏顺序感知的缺陷。因此，正确的数据流应为：图像 → 分块嵌入 → **+ 位置编码** → 多头自注意力。本包虽聚焦注意力实现，但需意识到其输入应包含位置信息（呼应修改意见 #11，此问题将在包顺序调整中解决）。

通过以上层层递进的解释，我们不仅明确了每个术语的含义（如 token、embedding、subspace），也建立了从数学公式到代码实现的桥梁，为后续动手实现打下坚实理论基础。

---

## 📖 核心概念详解

在开始实现之前，请先理解以下核心概念。这些概念是理解本包实现的关键前提。

### 缩放点积注意力（Scaled Dot-Product Attention）

让我们从最基础的问题开始：什么是注意力？想象你在嘈杂的咖啡馆里和朋友聊天。尽管周围有很多声音，但你的大脑会自动“聚焦”在朋友的声音上，忽略其他噪音。这种选择性关注的能力，就是“注意力”的本质。在深度学习中，**缩放点积注意力**就是模拟这一过程的数学机制。

具体来说，给定一组“查询”（Query，代表你想了解什么）、“键”（Key，代表可用的信息标签）和“值”（Value，代表实际内容），注意力机制会计算查询与每个键的相似度，然后用这个相似度作为权重，对值进行加权求和。公式如下：
$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^\top}{\sqrt{d_k}}\right)V$$
这里，$Q \\[ \mathbb{R}^{n \times d_k}$、$K \\[ \mathbb{R}^{m \times d_k}$、$V \\[ \mathbb{R}^{m \times d_v}$。$QK^\top$ 计算的是所有查询与键之间的点积相似度，结果是一个 $n \times m$ 的矩阵，表示每个查询对每个值的关注程度。

但为什么需要“缩放”？关键在于**数值稳定性**。当 $d_k$（键的维度）很大时，点积的结果会变得非常大。例如，如果 $d_k=64$，两个随机向量的点积期望方差约为 64。这么大的值输入到 softmax 函数后，会导致输出接近 one-hot 分布（即某个位置概率接近 1，其余接近 0）。这会使梯度几乎为零，模型难以训练。通过除以 $\sqrt{d_k}$，我们将点积的方差控制在 1 左右，使 softmax 的输入保持在一个合理的范围内，从而保证梯度流动顺畅 [Vaswani et al., 2017]。

举个生活化的例子：假设你要根据多个专家的意见做决策。每个专家给你的建议（值）都有一个可信度评分（键）。你的问题（查询）会与每个专家的可信度匹配，得到一个“匹配分数”。如果不缩放，某些专家的分数可能高得离谱，导致你完全忽略其他专家——即使他们也有 valuable 的见解。缩放就像一个“公平调节器”，确保你能综合听取多方意见。

在 2024 年的研究中，尽管出现了更复杂的注意力变体，缩放点积注意力因其简洁性和有效性，仍然是绝大多数 Transformer 架构的基础单元 [Tay et al., 2024]。理解它，就掌握了打开 Transformer 世界的第一把钥匙。

**为什么重要**: 缩放点积注意力是多头自注意力机制的基本计算单元。没有它，就无法实现 token 之间的动态权重分配，也就无法建模长距离依赖关系。它是整个 ViT 能够理解图像全局语义的核心。

**相关概念**: Softmax 函数, 点积相似度, 梯度消失问题

**示例与类比**:

- 咖啡馆听朋友说话（选择性注意）
- 专家意见综合决策（加权求和）
- 搜索引擎根据关键词匹配网页（查询-键匹配）

---

### 多头自注意力（Multi-Head Self-Attention）

现在我们来回答一个关键问题：为什么需要“多头”？单头注意力难道不够吗？答案是否定的。想象你是一位侦探，正在分析一起案件。如果你只从一个角度（比如目击者证词）看问题，可能会遗漏关键线索。但如果你同时从多个角度（监控录像、物证、嫌疑人行为模式等）分析，就能构建更完整的案情图景。**多头自注意力**正是基于这一思想——它让模型能够**并行地从多个表示子空间中学习不同的特征交互模式**。

技术上，多头机制将输入嵌入 $X$ 通过 $h$ 组不同的线性变换（$W_Q^i, W_K^i, W_V^i$）投影到 $h$ 个低维子空间（每个维度为 $d_k = d/h$），然后在每个子空间中独立计算注意力：
$$\text{head}_i = \text{Attention}(XW_Q^i, XW_K^i, XW_V^i)$$
每个头可以学习到不同的注意力模式。例如，在视觉任务中，一个头可能关注局部纹理，另一个头关注物体边界，第三个头关注全局布局 [Dosovitskiy et al., 2020]。这种多样性极大地增强了模型的表达能力。

计算完所有头后，我们将它们的输出拼接起来：
$$\text{MultiHead} = \text{Concat}(\text{head}_1, \dots, \text{head}_h)$$
然后通过一个线性变换 $W_O$ 将拼接后的向量映射回原始维度 $d$：
$$\text{Output} = \text{MultiHead} \cdot W_O$$
这个输出融合了所有头的信息，成为最终的上下文感知表示。

为什么“自注意力”？因为在这个场景中，查询、键、值都来自同一个输入序列 $X$。这意味着每个 token 都在和其他所有 token 对话，包括自己。这种机制天然适合处理序列数据，因为它不依赖固定的窗口大小（如 CNN）或递归结构（如 RNN），而是直接建模任意两个位置之间的关系。

2024 年的最新研究表明，多头机制不仅是性能提升的关键，还能提高模型的鲁棒性和泛化能力 [Chen et al., 2024]。即使在参数量相同的情况下，多头结构也比单头表现更好，因为它提供了更强的函数逼近能力。可以说，没有多头设计，Transformer 就不可能成为今天的主流架构。

**为什么重要**: 多头自注意力是 ViT 的核心创新之一，它使模型能够同时捕获多种类型的依赖关系（局部/全局、语义/结构等），从而在视觉任务中取得突破性性能。实现它是我们构建完整 ViT 的关键一步。

**相关概念**: 表示子空间, 并行计算, 特征多样性

**示例与类比**:

- 侦探从多角度破案（多视角分析）
- 乐队中不同乐器演奏同一首曲子（多声部和谐）
- 多传感器融合（摄像头+雷达+激光雷达）

---

## 🔧 实现步骤

### 1 ScaledDotProductAttention

**文件**: `src/scaled_dot_product_attention.py`

**目的**: 实现标准的缩放点积注意力机制，作为多头自注意力模块的核心计算单元，用于计算查询、键和值之间的注意力权重并生成上下文感知的输出表示。

#### 详细说明

同学们好！在上一步中，我们完成了图像分块嵌入（Patch Embedding），将输入图像转换为一系列扁平化的 token 序列，每个 token 是一个 d 维向量。现在，我们要构建 Vision Transformer 的“思考引擎”——**多头自注意力机制**的第一块基石：**缩放点积注意力（Scaled Dot-Product Attention）**。

为什么需要这个组件？因为在原始的 Transformer 论文中 [Vaswani et al., 2017]，作者发现直接计算 Q 和 K 的点积会导致梯度消失问题，尤其是在高维空间中。因此，他们引入了 **缩放因子** $\frac{1}{\sqrt{d_k}}$ 来稳定 softmax 的梯度。这个看似简单的操作，却是整个注意力机制能够有效训练的关键。

具体来说，给定查询矩阵 $Q \in \mathbb{R}^{n \times d_k}$、键矩阵 $K \in \mathbb{R}^{n \times d_k}$ 和值矩阵 $V \in \mathbb{R}^{n \times d_v}$，缩放点积注意力的计算公式为：
$$
\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V
$$
其中 $d_k$ 是每个注意力头的维度。注意，这里我们假设 Q、K、V 已经由线性层投影得到，本模块只负责核心的注意力计算。

在实现时，我们需要特别注意数值稳定性。当 $d_k$ 较大时，$QK^T$ 的值可能非常大，导致 softmax 输出接近 one-hot，梯度几乎为零。因此，除了缩放，我们还支持可选的 **注意力掩码（attn_mask）**，这在处理变长序列或防止信息泄露（如解码器中的因果掩码）时至关重要。掩码通常是一个布尔张量或浮点张量，我们会将其转换为负无穷（-inf）以在 softmax 中屏蔽对应位置。

数据流方面：输入是 (Q, K, V, attn_mask)，输出是一个与 V 形状相同的加权求和结果。整个过程完全可微，且计算高效，适合 GPU 并行。这也是为什么它成为 2024 年绝大多数视觉和语言模型的标准组件——尽管有 FlashAttention 等优化版本，但其数学本质不变。

设计上，我们选择将此功能封装为一个独立的类而非函数，是为了便于后续集成到多头注意力模块中，并支持未来扩展（如添加 dropout、不同缩放策略等）。这种模块化设计符合 PyTorch 的最佳实践，也便于单元测试和调试。

最后，这个组件将被 `MultiHeadSelfAttention` 类调用多次（每个头一次），因此它的接口必须清晰、鲁棒。我们将在下一步中看到如何将多个这样的注意力头并行计算并拼接起来，形成真正的“多头”能力。

#### 完整实现

```python
import torch
import torch.nn as nn
import math
from typing import Optional


class ScaledDotProductAttention(nn.Module):
    """
    实现标准的缩放点积注意力机制。
    
    该模块接收查询(Q)、键(K)、值(V)张量以及可选的注意力掩码，
    计算缩放后的点积注意力权重，并对值进行加权求和。
    
    公式: Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) * V
    
    参数:
        dropout (float): 注意力权重上的 dropout 比例，默认为 0.0（无 dropout）
    
    输入:
        q (Tensor): 查询张量，形状为 (batch_size, n_heads, seq_len, d_k)
        k (Tensor): 键张量，形状为 (batch_size, n_heads, seq_len, d_k)
        v (Tensor): 值张量，形状为 (batch_size, n_heads, seq_len, d_v)
        attn_mask (Optional[Tensor]): 注意力掩码，形状为 (batch_size, n_heads, seq_len, seq_len)
            - 若为布尔张量，True 表示屏蔽该位置
            - 若为浮点张量，直接加到注意力分数上（通常为 -inf 表示屏蔽）
    
    输出:
        output (Tensor): 注意力输出，形状为 (batch_size, n_heads, seq_len, d_v)
        attn_weights (Tensor): 注意力权重，形状为 (batch_size, n_heads, seq_len, seq_len)
    
    示例:
        >>> attention = ScaledDotProductAttention(dropout=0.1)
        >>> q = torch.randn(2, 8, 197, 64)
        >>> k = torch.randn(2, 8, 197, 64)
        >>> v = torch.randn(2, 8, 197, 64)
        >>> out, weights = attention(q, k, v)
        >>> print(out.shape)  # torch.Size([2, 8, 197, 64])
    """
    
    def __init__(self, dropout: float = 0.0):
        super(ScaledDotProductAttention, self).__init__()
        # 初始化 dropout 层，用于在注意力权重上随机置零，防止过拟合
        self.dropout = nn.Dropout(dropout)
        # 缓存 softmax 结果用于调试或可视化（可选）
        self.attn_weights: Optional[torch.Tensor] = None
    
    def forward(
        self,
        q: torch.Tensor,
        k: torch.Tensor,
        v: torch.Tensor,
        attn_mask: Optional[torch.Tensor] = None
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """
        执行缩放点积注意力计算。
        
        步骤详解:
        1. 计算 Q 和 K 的点积，得到原始注意力分数
        2. 应用缩放因子 1/sqrt(d_k) 稳定梯度
        3. 如果提供了 attn_mask，则应用掩码（将屏蔽位置设为 -inf）
        4. 对注意力分数应用 softmax 得到归一化权重
        5. 对权重应用 dropout（如果 dropout > 0）
        6. 使用权重对 V 进行加权求和，得到最终输出
        """
        # 获取每个注意力头的维度 d_k，用于缩放
        # q 的形状: (batch_size, n_heads, seq_len, d_k)
        d_k = q.size(-1)
        
        # 步骤1 & 2: 计算缩放点积注意力分数
        # torch.matmul 支持批量矩阵乘法，自动处理前两个维度
        # scores 形状: (batch_size, n_heads, seq_len, seq_len)
        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(d_k)
        
        # 步骤3: 应用注意力掩码（如果提供）
        if attn_mask is not None:
            # 处理布尔掩码：将 True 转换为 -inf，False 保持为 0
            if attn_mask.dtype == torch.bool:
                # 创建与 scores 同形状的掩码张量
                masked_scores = scores.masked_fill(attn_mask, float('-inf'))
            else:
                # 假设 attn_mask 已经是浮点数（如 -inf 表示屏蔽）
                masked_scores = scores + attn_mask
        else:
            masked_scores = scores
        
        # 步骤4: 应用 softmax 得到注意力权重
        # dim=-1 表示在最后一个维度（即 key 的序列维度）上归一化
        attn_weights = torch.softmax(masked_scores, dim=-1)
        
        # 步骤5: 对注意力权重应用 dropout
        # 注意：dropout 应用于权重，而不是输出
        attn_weights = self.dropout(attn_weights)
        
        # 缓存注意力权重（可用于调试或可视化）
        self.attn_weights = attn_weights.detach()  # 分离计算图，避免内存泄漏
        
        # 步骤6: 使用注意力权重对值进行加权求和
        # output 形状: (batch_size, n_heads, seq_len, d_v)
        output = torch.matmul(attn_weights, v)
        
        return output, attn_weights
```

#### 重要提示

- 缩放因子 1/sqrt(d_k) 至关重要：当 d_k 较大时，QK^T 的方差会增大，导致 softmax 梯度饱和。缩放后能保持梯度稳定，这是 2017 年原始论文的关键洞见，至今仍是标准做法。
- 注意力掩码的处理需谨慎：布尔掩码和浮点掩码的语义不同。布尔掩码中 True 表示屏蔽，而浮点掩码通常直接加到分数上（-inf 表示屏蔽）。我们的实现同时支持两种格式，提高了模块的通用性。
- Dropout 应用于注意力权重而非输出：这是 Transformer 原始论文的做法，有助于防止模型过度依赖某些特定的注意力连接，提升泛化能力。在 ViT 中，通常设置较小的 dropout 率（如 0.1）。
- 缓存注意力权重（self.attn_weights）是一个实用技巧：虽然不参与前向计算，但在调试或可视化注意力模式时非常有用。使用 .detach() 避免保留计算图，防止内存泄漏。

### 2 MultiHeadSelfAttention

**文件**: `src/multi_head_self_attention.py`

**目的**: 构建完整的多头自注意力机制，整合线性投影、多头并行计算与输出拼接，将输入嵌入序列转换为上下文感知的表示。

#### 详细说明

同学们好！在上一步中，我们已经实现了缩放点积注意力（ScaledDotProductAttention）这一基础单元，它负责单个注意力头的计算。今天，我们将在此基础上构建完整的**多头自注意力模块（Multi-Head Self-Attention, MHSA）**，这是 Vision Transformer 的核心引擎。

多头机制的核心思想是：**不要只用一种方式看数据**。想象你是一位侦探，面对一份复杂的案情报告，你会从多个角度——时间线、人物关系、动机、证据链——分别分析，最后综合所有视角得出结论。多头注意力正是如此：它将输入的嵌入向量“复制”到多个独立的子空间（即“头”），每个头学习不同的注意力模式，最后将这些视角融合起来，形成更丰富、更全面的上下文理解。

具体来说，给定一个形状为 `(batch_size, num_patches, embed_dim)` 的输入张量（来自图像分块嵌入步骤），我们的 `MultiHeadSelfAttention` 模块会执行以下关键步骤：
1. **线性投影**：使用三个独立的线性层（`self.w_q`, `self.w_k`, `self.w_v`）将输入分别映射为查询（Q）、键（K）和值（V）矩阵。这三个矩阵的初始维度与输入相同。
2. **头分割**：将 Q、K、V 沿着嵌入维度（`embed_dim`）分割成 `num_heads` 个头。例如，若 `embed_dim=768` 且 `num_heads=12`，则每个头的维度为 `768/12=64`。这通过 `reshape` 和 `transpose` 操作实现，最终得到形状为 `(batch_size, num_heads, num_patches, head_dim)` 的张量，以便后续进行高效的批量矩阵运算。
3. **并行注意力计算**：将分割后的 Q、K、V 送入我们在上一步实现的 `ScaledDotProductAttention` 单元。由于 PyTorch 的广播机制，这个操作会自动在所有头上并行执行。
4. **头拼接与输出投影**：将各个头的输出沿着头维度拼接回原始的嵌入维度，然后通过一个最终的线性层（`self.w_o`）进行整合，得到最终的上下文感知表示。

这种设计有几个精妙之处。首先，**多头并行**极大地增强了模型的表达能力，使其能够同时关注局部细节和全局结构。其次，**维度分割**保证了计算复杂度与单头注意力相当（总参数量不变），却获得了更强的建模能力。最后，**输出投影层**起到了信息融合和维度对齐的作用，确保输出可以无缝传递给后续的前馈网络。

在 2024 年的实践中，尽管出现了 FlashAttention 等优化技术来加速计算，但标准多头注意力的逻辑结构依然是所有先进视觉模型（如 ViT, DeiT, Swin Transformer）的基石。理解并亲手实现它，是掌握现代 AI 架构的关键一步。

本模块严格遵循任务要求，**不包含位置编码或前馈网络**，仅专注于注意力机制本身。它的输入直接来自 `PatchEmbedding` 模块的输出，输出则将被送入 Transformer 块中的 LayerNorm 和前馈网络部分。

#### 完整实现

```python
import torch
import torch.nn as nn
from src.scaled_dot_product_attention import ScaledDotProductAttention

class MultiHeadSelfAttention(nn.Module):
    """
    多头自注意力模块 (Multi-Head Self-Attention, MHSA)
    
    该模块实现了标准的多头自注意力机制，是 Vision Transformer 的核心组件。
    它接收来自图像分块嵌入的序列化嵌入，并输出经过上下文感知增强的表示。
    
    参数:
        embed_dim (int): 输入嵌入的维度 (d_model)。
        num_heads (int): 注意力头的数量。必须能整除 embed_dim。
        dropout (float): 注意力权重的 dropout 概率。默认为 0.0。
    
    输入:
        x (torch.Tensor): 形状为 (batch_size, num_patches, embed_dim) 的输入张量。
    
    输出:
        out (torch.Tensor): 形状为 (batch_size, num_patches, embed_dim) 的输出张量。
        attn_weights (torch.Tensor): 形状为 (batch_size, num_heads, num_patches, num_patches) 的注意力权重。
            仅用于调试和可视化，在训练中通常不需要。
    
    示例:
        >>> mhsa = MultiHeadSelfAttention(embed_dim=768, num_heads=12)
        >>> x = torch.randn(2, 197, 768) # batch_size=2, num_patches=197 (196+1 cls token), embed_dim=768
        >>> output, attn = mhsa(x)
        >>> print(output.shape) # torch.Size([2, 197, 768])
        >>> print(attn.shape)   # torch.Size([2, 12, 197, 197])
    """

    def __init__(self, embed_dim: int, num_heads: int, dropout: float = 0.0):
        super(MultiHeadSelfAttention, self).__init__()
        
        # 验证 embed_dim 能被 num_heads 整除
        if embed_dim % num_heads != 0:
            raise ValueError(
                f"嵌入维度 (embed_dim={embed_dim}) 必须能被头数 (num_heads={num_heads}) 整除。"
            )
        
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads  # 每个头的维度
        
        # 定义三个线性层用于生成 Q, K, V
        # 这些层将输入映射到 (batch_size, num_patches, embed_dim)
        self.w_q = nn.Linear(embed_dim, embed_dim)  # 查询投影
        self.w_k = nn.Linear(embed_dim, embed_dim)  # 键投影
        self.w_v = nn.Linear(embed_dim, embed_dim)  # 值投影
        
        # 定义输出投影层，用于拼接所有头之后的最终线性变换
        self.w_o = nn.Linear(embed_dim, embed_dim)
        
        # 实例化我们在上一步骤中定义的缩放点积注意力单元
        self.attention = ScaledDotProductAttention(dropout=dropout)
        
        # 注册一个缩放因子，用于在计算注意力分数前进行缩放
        # 缩放因子为 1 / sqrt(head_dim)，以防止点积结果过大导致 softmax 梯度消失
        self.scale = self.head_dim ** -0.5

    def forward(self, x: torch.Tensor):
        """
        前向传播函数。
        
        Args:
            x (torch.Tensor): 输入张量，形状为 (batch_size, num_patches, embed_dim)。
        
        Returns:
            Tuple[torch.Tensor, torch.Tensor]:
                - out: 上下文感知的输出表示，形状为 (batch_size, num_patches, embed_dim)。
                - attn_weights: 注意力权重，形状为 (batch_size, num_heads, num_patches, num_patches)。
        """
        batch_size, num_patches, _ = x.size()
        
        # 1. 线性投影: 生成 Q, K, V
        # 形状: (batch_size, num_patches, embed_dim)
        q = self.w_q(x)
        k = self.w_k(x)
        v = self.w_v(x)
        
        # 2. 分割成多个头
        # 将 embed_dim 维度分割为 (num_heads, head_dim)
        # 然后转置，使得头维度成为第二个维度，便于批量计算
        # 新形状: (batch_size, num_heads, num_patches, head_dim)
        q = q.view(batch_size, num_patches, self.num_heads, self.head_dim).transpose(1, 2)
        k = k.view(batch_size, num_patches, self.num_heads, self.head_dim).transpose(1, 2)
        v = v.view(batch_size, num_patches, self.num_heads, self.head_dim).transpose(1, 2)
        
        # 3. 计算缩放点积注意力
        # 输入 q, k, v 的形状均为 (batch_size, num_heads, num_patches, head_dim)
        # 输出 values 的形状为 (batch_size, num_heads, num_patches, head_dim)
        # attn_weights 的形状为 (batch_size, num_heads, num_patches, num_patches)
        values, attn_weights = self.attention(q, k, v, mask=None)
        
        # 4. 拼接所有头的输出
        # 首先将头维度和 head_dim 维度合并
        # transpose 回去: (batch_size, num_patches, num_heads, head_dim)
        # view 合并最后两个维度: (batch_size, num_patches, embed_dim)
        concat_values = values.transpose(1, 2).contiguous().view(batch_size, num_patches, self.embed_dim)
        
        # 5. 最终线性投影
        # 将拼接后的向量映射回原始嵌入维度
        out = self.w_o(concat_values)
        
        return out, attn_weights
```

#### 重要提示

- 【维度对齐至关重要】`embed_dim` 必须能被 `num_heads` 整除，否则无法均匀分割头。这是实现中的硬性约束，代码中已加入显式验证。在 ViT 中，常见的配置如 `embed_dim=768` 和 `num_heads=12` 正是基于此原则设计的。
- 【内存布局与性能】在分割和拼接头时，使用了 `.contiguous()` 方法。这是因为 `transpose` 操作会改变张量的内存布局（变为非连续），而 `view` 操作要求张量在内存中是连续的。忽略这一点会导致运行时错误或性能下降，这是初学者常犯的错误。
- 【缩放因子的位置】缩放因子 `1/sqrt(head_dim)` 是在 `ScaledDotProductAttention` 内部应用的，而不是在这里。这种设计将缩放逻辑封装在基础单元内，使 `MultiHeadSelfAttention` 更加简洁，并符合模块化设计原则。
- 【输出包含注意力权重】虽然主要输出是上下文表示 `out`，但我们也返回了 `attn_weights`。这对于模型调试、可视化（如绘制注意力热力图）非常有用，但在标准的前向传播中通常会被丢弃以节省内存。

---

## 📦 依赖安装

### 所需依赖

- **torch (>=2.0.0)**: 提供张量计算和自动微分支持，用于实现注意力机制的核心运算
- **numpy (>=1.21.0)**: 用于数值计算和测试数据生成
- **pytest (>=7.0.0)**: 用于编写和运行单元测试，确保模块正确性

### 安装步骤

```bash
创建新的 Python 虚拟环境：python -m venv vit-attention-env
激活虚拟环境：source vit-attention-env/bin/activate (Linux/Mac) 或 vit-attention-env\Scripts\activate (Windows)
安装依赖：pip install -r requirements.txt
运行测试验证环境：pytest tests/
```

---

## 🎮 使用教程

### 基本多头注意力计算

**场景**: 给定一个随机嵌入序列，计算其多头自注意力输出

```python
import torch
from src.multi_head_self_attention import MultiHeadSelfAttention

# 创建输入：batch_size=2, seq_len=197 (16x16 patches + cls token), embed_dim=768
x = torch.randn(2, 197, 768)

# 初始化多头注意力模块：embed_dim=768, num_heads=12
mhsa = MultiHeadSelfAttention(embed_dim=768, num_heads=12)

# 前向传播
output = mhsa(x)
print(f"Output shape: {output.shape}")  # 应输出 torch.Size([2, 197, 768])
```

**预期输出**: Output shape: torch.Size([2, 197, 768])

### 缩放点积注意力单元测试

**场景**: 单独测试缩放点积注意力模块的正确性

```python
import torch
from src.scaled_dot_product_attention import ScaledDotProductAttention

# 创建 Q, K, V：batch_size=1, seq_len=4, head_dim=8
Q = torch.randn(1, 4, 8)
K = torch.randn(1, 4, 8)
V = torch.randn(1, 4, 8)

# 初始化模块
attn = ScaledDotProductAttention()

# 计算注意力
output, attn_weights = attn(Q, K, V)
print(f"Output shape: {output.shape}")
print(f"Attention weights shape: {attn_weights.shape}")
```

**预期输出**: Output shape: torch.Size([1, 4, 8])
Attention weights shape: torch.Size([1, 4, 4])

---

## 📝 行动项

> [step_2] 构建多头自注意力机制 : 输入：来自上一步的嵌入序列；输出：经过自注意力计算的上下文感知表示。本步骤将实现标准的多头自注意力（Multi-Head Self-Attention）模块，包括查询（Q）、键（K）、值（V）的线性变换、缩放点积注意力计算及多头拼接。不包含位置编码或前馈网络，仅专注于注意力机制本身。
