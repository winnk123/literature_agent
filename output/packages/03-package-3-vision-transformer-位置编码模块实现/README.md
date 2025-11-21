# Package 3: Vision Transformer 位置编码模块实现

## 📋 概述

同学们好！在本教程中，我们将聚焦于 Vision Transformer 架构中至关重要的**位置编码**（Position Encoding）模块。由于 Transformer 本身不具备对输入序列顺序的感知能力，我们必须显式地注入空间位置信息，以保留图像分块后的原始空间结构。本包将实现两种主流的位置编码方式：经典的正弦余弦固定编码和可学习的参数化编码，并提供一个灵活的融合器，将位置信息加到嵌入序列上。这一模块虽小，却是 ViT 能够理解“哪里是什么”的关键所在，为后续的自注意力机制提供有序输入。

## 📂 项目结构

```
package-03-vit-position-encoding/
├── README.md
├── requirements.txt
├── src/
│   ├── sinusoidal_position_encoding.py
│   ├── learned_position_encoding.py
│   └── position_encoding_adder.py
├── configs/
│   └── config.yaml
└── tests/
    └── test_position_encoding.py
```

## 💡 理论基础

同学们，今天我们深入探讨 Vision Transformer（ViT）中一个看似简单却极其关键的组件——**位置编码**（Positional Encoding）。为了帮助大家从零开始理解这一概念，我们将从基础术语回顾入手，逐步展开其原理、数学形式、二维图像适配策略，并对比不同实现方式的优劣。

### Key Concepts Recap

在深入位置编码之前，我们先快速回顾几个核心概念：

1. **嵌入向量**（Embedding Vectors）：在 ViT 中，输入图像首先被划分为固定大小的图像块（例如 16×16 像素），每个图像块通过一个线性投影层（通常是一个卷积或全连接层）转换为一个固定维度的向量，称为“嵌入向量”。这些向量构成了模型后续处理的基本单元。

2. **Token 的含义**：在自然语言处理（NLP）中，token 指的是单词或子词单元；而在 ViT 中，每个图像块就相当于一个“视觉 token”。因此，一张图像被转换为一个 token 序列，类似于一句话被拆分为单词序列。

3. **自注意力机制的局限性**：自注意力机制的核心思想是让每个 token 能够“关注”序列中的所有其他 token，并根据它们的相关性动态加权。然而，**自注意力本身对输入顺序完全不敏感**——它只计算 token 之间的相似度，而不知道“A 块在 B 块左边”或“C 块在顶部”。如果没有位置信息，打乱图像块的顺序不会改变自注意力的输出，这显然会严重损害模型对空间结构的理解能力。

### 为什么需要位置编码？

想象你有一副拼图，但所有碎片都被随机打乱。即使你能识别每一块上的图案（即嵌入向量的内容），如果你不知道它们原本的位置关系，就无法还原整幅图像。Transformer 架构天生缺乏对序列顺序的感知能力，因此必须显式地注入位置信息。位置编码的作用就是为每个 token 添加一个“地址标签”，告诉模型“我在哪里”。

### 两类主流位置编码方法

目前主要有两种位置编码策略：**可学习位置编码**（Learned Positional Embedding）和**固定正弦余弦编码**（Sinusoidal Positional Encoding）。

#### 1. 可学习位置编码

这是 ViT 论文 [Dosovitskiy et al., 2020] 采用的方法。其思想非常直接：为序列中的每一个可能位置（例如最多支持 N 个图像块）分配一个可训练的向量。假设嵌入维度为 $d$，最大序列长度为 $L$，则模型会初始化一个形状为 $(L, d)$ 的参数矩阵 $\mathbf{P}$。在前向传播时，第 $i$ 个图像块的嵌入向量 $\mathbf{x}_i$ 会加上对应的位置向量 $\mathbf{p}_i$，即：
$$
\mathbf{z}_i = \mathbf{x}_i + \mathbf{p}_i
$$
这些位置向量在训练过程中通过反向传播自动优化，模型可以自由学习最适合任务的位置表示。优点是灵活、数据驱动；缺点是泛化能力受限于训练时的最大序列长度，且无法外推到更长序列。

#### 2. 正弦余弦位置编码（固定编码）

该方法源自原始 Transformer 论文 [Vaswani et al., 2017]，使用确定性的三角函数生成位置编码，无需训练。对于一维序列中的位置 $p$ 和嵌入维度 $d$，其定义如下：
$$
PE_{(p, 2i)} = \sin\left(\frac{p}{10000^{2i/d}}\right), \quad PE_{(p, 2i+1)} = \cos\left(\frac{p}{10000^{2i/d}}\right)
$$
其中 $i = 0, 1, ..., d/2 - 1$。这种设计确保了每个维度对应不同频率的正弦波，低频分量编码全局位置，高频分量编码局部细节。更重要的是，由于使用了相对位置的线性组合性质，模型理论上可以泛化到比训练时更长的序列。

然而，这里有一个关键前提：**该公式仅适用于一维序列**。而图像块天然排列在二维网格上（行和列），这就引出了下一个核心问题。

### 二维位置编码：从图像网格到序列索引

在 ViT 中，图像被划分为 $H \times W$ 的网格（例如 14×14），共 $N = H \times W$ 个图像块。为了将其输入到 Transformer 中，这些二维坐标必须映射为一维序列。最常用的方法是**行优先展平**（row-major flattening）：将第 $(r, c)$ 位置的图像块映射到序列索引 $p = r \cdot W + c$。这样，二维位置就被压缩为一个一维索引，可以直接使用上述一维位置编码方法。

但这种方法忽略了图像的二维结构——水平相邻和垂直相邻的块在语义上可能具有不同的空间关系。因此，一些改进方案提出使用**独立的行列编码**：分别为行位置 $r$ 和列位置 $c$ 生成两个位置向量 $\mathbf{p}^r$ 和 $\mathbf{p}^c$，然后相加得到最终编码：
$$
\mathbf{p}_{(r,c)} = \mathbf{p}^r_r + \mathbf{p}^c_c
$$
这种方式能更好地保留二维空间信息，但在标准 ViT 中并未采用，而是依赖行优先展平配合可学习的一维位置编码。

### 总结与选择

- **可学习编码**：简单有效，适合固定输入尺寸的任务（如 ImageNet 分类），是 ViT 的默认选择。
- **正弦编码**：具备外推潜力，但需注意其一维本质；若用于图像，通常仍需先进行二维到一维的映射。
- **关键点**：无论哪种方法，位置编码都必须在输入自注意力机制**之前**加到 patch embeddings 上，否则自注意力将无法利用空间顺序信息。

理解这些原理后，我们将在实现中看到如何构建这两种编码，并通过 `PositionEncodingAdder` 模块灵活集成它们。

---

## 📖 核心概念详解

在开始实现之前，请先理解以下核心概念。这些概念是理解本包实现的关键前提。

### 正弦余弦位置编码 (Sinusoidal Positional Encoding)

想象一下，你是一位指挥家，需要给乐队里每一位乐手分配一个独特的“声音签名”，这样即使他们演奏相同的音符，你也能分辨出是谁在演奏。正弦余弦位置编码就是为序列中的每个位置（比如第1个、第2个...第N个图像块）分配这样一个独特的“签名”。

这个“签名”不是一个随机的数字，而是一组精心设计的、由正弦和余弦函数生成的数值。它的核心公式是这样的：对于序列中的第 $p$ 个位置，以及嵌入向量的第 $i$ 维，我们计算：
$$PE_{(p, i)} = \begin{cases} 
\sin\left(\frac{p}{10000^{i/d}}\right) & \text{if } i \text{ is even} \\
\cos\left(\frac{p}{10000^{(i-1)/d}}\right) & \text{if } i \text{ is odd}
\end{cases}$$
这里，$d$ 是嵌入向量的总维度。你会发现，随着维度 $i$ 的增加，分母 $10000^{i/d}$ 会变得越来越大，这意味着函数的“波长”会越来越长。低维度的编码变化很快（高频），捕捉精细的位置差异；高维度的编码变化很慢（低频），捕捉粗略的位置范围。

这种设计最神奇的地方在于它能编码**相对位置**。假设你想知道位置 $p+k$ 相对于位置 $p$ 的编码是什么。利用三角函数的和角公式，$PE_{p+k}$ 可以被表示为 $PE_p$ 和 $PE_k$ 的一个线性组合。这意味着，模型可以通过学习一个固定的线性变换，来处理任意长度的相对位移，从而具备了**外推能力**（Extrapolation Ability）——即使在训练时没见过这么长的序列，它也能大致理解新位置的关系。这是 [Vaswani et al., 2017] 论文中强调的一个关键优势。

在视觉任务中，虽然图像是二维的，但我们通常会将二维位置 $(row, col)$ 先展平成一维索引 $p = row \times width + col$，然后再应用上述一维编码。这是一种简单有效的近似。当然，也有更复杂的二维正弦编码变体，但基础的一维版本因其简洁性和有效性，仍然是许多模型的首选。理解这个编码的数学原理，能帮助我们明白为什么 Transformer 能在没有循环或卷积结构的情况下，依然能处理有序数据。

**为什么重要**: 正弦余弦位置编码是 Transformer 架构的基石之一。在本项目中，它是位置编码的一种核心实现方案。理解其工作原理，不仅能让我们正确地实现它，更能让我们明白为什么这种看似简单的加法操作，能够赋予模型理解序列顺序的能力。这对于调试模型、理解其行为至关重要。

**相关概念**: 可学习位置编码, 序列建模, 归纳偏置

**示例与类比**:

- 想象一串圣诞树上的彩灯，每个灯泡都有一个独特的闪烁频率（由正弦/余弦函数决定）。即使所有灯泡颜色一样，你也能通过它们的闪烁模式分辨出哪个是第一个，哪个是最后一个。
- 就像给图书馆里的每一本书贴上一个条形码，这个条形码不是随机的，而是根据书架的行和列，用一套数学规则生成的，这样扫描仪不仅能识别书，还能知道它大概在哪个区域。

---

### 可学习位置编码 (Learned Positional Embedding)

现在，让我们换一种思路。与其用一个固定的数学公式（如正弦余弦）来给每个位置分配“签名”，为什么不直接让模型自己去“发明”一套最适合当前任务的签名系统呢？这就是**可学习位置编码**的核心思想。

在技术上，这非常直观。我们不再计算任何函数，而是直接创建一个**查找表**（Lookup Table）。这个表是一个形状为 `(max_positions, embedding_dim)` 的矩阵，我们可以称之为 `position_embedding`。其中，`max_positions` 是我们预期序列的最大长度（比如，一张 224x224 的图片被切成 16x16 的块，就会有 196 个块，再加上一个 class token，总共 197 个位置）。`embedding_dim` 则是每个嵌入向量的维度，必须和来自图像分块模块的嵌入维度完全一致。

在模型初始化时，我们会用某种策略（比如从正态分布中随机采样）来填充这个矩阵的初始值。然后，在整个训练过程中，这个矩阵会像神经网络的权重一样，通过**反向传播**和**梯度下降**算法进行更新。模型会不断调整每个位置对应的嵌入向量，直到找到一种表示方式，使得加上这个位置信息后，最终的分类或检测任务能达到最好的效果。

这种方法的最大优点就是**灵活性和数据驱动**。它没有任何预设的关于位置应该如何表示的偏见。如果任务需要模型特别关注角落的块，或者对中心区域有特殊的敏感性，可学习编码都能通过训练过程自动捕捉到这些模式。Vision Transformer 的原始论文 [Dosovitskiy et al., 2020] 正是采用了这种策略，并证明了其在大规模图像分类任务上的有效性。

然而，这种灵活性也带来了代价。首先，它失去了正弦余弦编码的外推能力。如果在推理时遇到比训练时更长的序列（`max_positions` 不够大），模型就无法处理，因为查找表里没有对应的新位置的编码。其次，它增加了模型的参数量，尽管这部分参数通常占比很小。最近的研究，如 [Liu et al., 2024] 探讨了混合策略，即在可学习编码的基础上加入一些固定的归纳偏置，以期结合两者的优点。但在我们的基础实现中，我们将忠实还原这种纯粹的、端到端可学习的方式。

**为什么重要**: 可学习位置编码是现代 ViT 实现中最常用的方法。在本项目中，它是另一种核心的位置编码方案。掌握其实现方式，意味着我们能够构建一个完全由数据驱动、可端到端训练的 ViT 模型。理解其与固定编码的区别，有助于我们在不同场景下做出合适的选择。

**相关概念**: 正弦余弦位置编码, 嵌入层 (Embedding Layer), 模型参数, 端到端学习

**示例与类比**:

- 这就像给一支新组建的足球队分配球衣号码。教练（模型）不是按照身高或年龄（固定规则）来分配，而是在训练和比赛中观察每个球员的特点和场上位置，然后动态地调整号码，使得看到号码就能联想到该球员的战术作用。
- 类似于一个智能翻译软件，它不使用固定的词典，而是在大量双语语料上训练，自己学习每个词在不同上下文中的最佳表示方式。位置编码也是让模型自己学习‘位置’这个词的最佳表示。

---

## 🔧 实现步骤

### 1 SinusoidalPositionEncoding

**文件**: `src/sinusoidal_position_encoding.py`

**目的**: 实现基于正弦和余弦函数的固定位置编码，为嵌入序列注入可区分的位置信息，从而保留图像分块后的空间顺序。

#### 详细说明

同学们好！在上一步（步骤1）中，我们已经完成了图像分块嵌入（Patch Embedding），将输入图像转换为一系列一维嵌入向量组成的序列。然而，这些嵌入向量本身是**无序的**——Transformer 架构无法感知“A块在B块左边”这样的空间关系。因此，我们必须显式地为每个位置注入唯一的位置信息，这就是本步骤要解决的核心问题。

今天我们要实现的是 **SinusoidalPositionEncoding**（正弦余弦位置编码）。虽然现代 Vision Transformer 更常使用可学习的位置编码（将在后续步骤介绍），但理解这种经典的固定编码方式非常重要，因为它揭示了如何通过数学函数显式建模位置信息，并具备外推到更长序列的能力。

### 模块结构图
```
输入嵌入序列 (B, L, D)
        ↓
预计算位置编码矩阵 (L_max, D)
        ↓
截取前 L 行 → 广播至批次维度
        ↓
逐元素相加：嵌入 + 位置编码
        ↓
输出带位置信息的序列 (B, L, D)
```

### 伪代码
```
初始化：embed_dim, max_seq_len
创建位置索引 pos = [0, 1, 2, ..., max_seq_len-1]  # 形状 (max_seq_len, 1)
创建维度索引 i = [0, 1, 2, ..., embed_dim-1]      # 形状 (1, embed_dim)

计算角度频率：
    angle_rates = 1 / (10000 ^ (i / embed_dim))   # 形状 (1, embed_dim)
    angle_rads = pos * angle_rates                # 形状 (max_seq_len, embed_dim)

对偶数维度应用 sin，奇数维度应用 cos：
    PE[:, 0::2] = sin(angle_rads[:, 0::2])
    PE[:, 1::2] = cos(angle_rads[:, 1::2])

前向传播时：
    输入 x (B, L, D)
    取 PE 的前 L 行 → (L, D)
    广播加到 x 上 → (B, L, D)
```

### 关键公式说明
对于序列中第 `pos` 个位置、嵌入维度中的第 `i` 维，其编码值定义如下：
- 当 `i` 为偶数时：PE(pos, i) = sin(pos / 10000^(i/embed_dim))
- 当 `i` 为奇数时：PE(pos, i) = cos(pos / 10000^((i-1)/embed_dim))

这种设计使得不同频率的正弦/余弦波覆盖从高频（低维）到低频（高维）的变化，从而能表示绝对位置和相对位置关系。

### 为什么先讲这个？
尽管可学习编码更简单直观，但正弦余弦编码展示了**无需参数即可编码位置**的巧妙思想，并且其周期性结构有助于模型泛化到训练时未见过的序列长度。理解它有助于我们更深入把握位置信息的本质。

#### 完整实现

```python
import torch
import torch.nn as nn
import math

class SinusoidalPositionEncoding(nn.Module):
    """
    正弦余弦位置编码模块。
    
    该模块根据 Vaswani et al. (2017) 提出的经典方法，为输入序列生成固定的位置编码。
    编码基于正弦和余弦函数，无需训练参数，适用于任意长度（不超过 max_seq_len）的序列。
    
    参数:
        embed_dim (int): 嵌入向量的维度（必须为偶数，因编码按奇偶维度分配）
        max_seq_len (int): 支持的最大序列长度（默认 5000，足够覆盖大多数 ViT 场景）
    
    输入:
        x (torch.Tensor): 形状为 (batch_size, seq_len, embed_dim) 的嵌入序列
    
    输出:
        torch.Tensor: 形状为 (batch_size, seq_len, embed_dim) 的带位置编码的序列
    """
    
    def __init__(self, embed_dim: int, max_seq_len: int = 5000):
        super().__init__()
        if embed_dim % 2 != 0:
            raise ValueError(f"embed_dim 必须为偶数，当前值: {embed_dim}")
        
        # 创建位置索引 [0, 1, 2, ..., max_seq_len-1] -> (max_seq_len, 1)
        position = torch.arange(0, max_seq_len, dtype=torch.float).unsqueeze(1)
        
        # 计算维度索引 i 对应的分母项: 10000^(i/embed_dim)
        # 注意：这里对偶数和奇数维度统一处理，通过除以2来匹配公式
        div_term = torch.exp(
            torch.arange(0, embed_dim, 2, dtype=torch.float) * 
            (-math.log(10000.0) / embed_dim)
        )
        
        # 初始化位置编码矩阵 (max_seq_len, embed_dim)
        pe = torch.zeros(max_seq_len, embed_dim)
        
        # 偶数维度使用 sin
        pe[:, 0::2] = torch.sin(position * div_term)
        # 奇数维度使用 cos
        pe[:, 1::2] = torch.cos(position * div_term)
        
        # 注册为 buffer，不参与梯度更新，但会随设备移动
        self.register_buffer('pe', pe)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        将位置编码加到输入嵌入上。
        
        Args:
            x: 输入张量，形状 (batch_size, seq_len, embed_dim)
            
        Returns:
            带位置编码的张量，形状 (batch_size, seq_len, embed_dim)
        """
        seq_len = x.size(1)
        # 检查序列长度是否超出预设最大长度
        if seq_len > self.pe.size(0):
            raise ValueError(
                f"输入序列长度 ({seq_len}) 超过最大支持长度 ({self.pe.size(0)})"
            )
        
        # 取前 seq_len 个位置编码，并扩展批次维度以进行广播
        # self.pe[:seq_len, :] 形状: (seq_len, embed_dim)
        # x 形状: (batch_size, seq_len, embed_dim)
        return x + self.pe[:seq_len, :].unsqueeze(0)
```

#### 重要提示

- 【维度必须为偶数】正弦余弦编码要求 embed_dim 为偶数，因为编码在偶数和奇数维度上分别使用 sin 和 cos。如果尝试使用奇数维度（如 769），会因索引越界导致错误。在 ViT 中，标准配置如 768、1024 都是偶数，所以通常不会有问题，但自定义模型时需特别注意。
- 【预计算 vs 实时计算】我们选择在初始化时预计算整个位置编码矩阵，而不是在 forward 中实时计算。这是因为三角函数计算开销较大，预计算可显著提升推理速度（尤其在长序列场景）。虽然占用少量内存（max_seq_len * embed_dim * 4 字节），但对于现代 GPU 来说微不足道。
- 【广播机制的妙用】在 forward 中，我们通过 unsqueeze(0) 将 (seq_len, embed_dim) 扩展为 (1, seq_len, embed_dim)，这样就能与 (batch_size, seq_len, embed_dim) 的输入自动广播相加。这是 PyTorch 中高效处理 batch 数据的标准技巧，避免了显式的循环或重复堆叠。
- 【与可学习编码的对比】此实现是固定的（fixed），而可学习位置编码（将在 learned_position_encoding.py 中实现）会创建一个可训练的嵌入表。2024 年的研究（如《On the Role of Positional Encoding in Vision Transformers》）表明，在大规模数据集上两者性能接近，但在小数据集上可学习编码可能略优。建议根据任务需求选择。

### 2 LearnedPositionEncoding

**文件**: `src/learned_position_encoding.py`

**目的**: 提供可训练的位置编码，通过参数学习的方式为嵌入序列添加位置信息。

#### 详细说明

同学们好！在上一步（步骤1）中，我们已经实现了经典的正弦余弦位置编码（SinusoidalPositionEncoding），它是一种**固定、不可学习**的编码方式。今天我们要实现的是另一种主流方案——**可学习位置编码**（Learned Position Encoding）。这种编码方式不再依赖预定义的数学函数，而是将每个位置的编码向量作为模型参数，在训练过程中与其他权重一起优化。这种方法在 Vision Transformer（ViT）等现代架构中被广泛采用，因为它赋予了模型更大的灵活性去适应特定任务的空间结构。

那么，为什么我们需要可学习的位置编码呢？回想一下，Transformer 架构本身对输入序列的顺序是“盲”的。当我们把图像切成 N 个块并展平成一维序列后，模型必须知道第 i 个块原本在图像中的哪个位置。正弦余弦编码虽然能提供良好的泛化性（甚至能处理比训练时更长的序列），但它是一种通用的、任务无关的先验。而可学习编码则允许模型根据具体任务（比如图像分类、目标检测）去“定制”最适合的位置表示，这在实践中往往能带来更好的性能，尤其是在数据充足的情况下。

我们的实现核心非常简洁：使用 PyTorch 的 `nn.Embedding` 层。这个层本质上是一个查找表（lookup table），它将整数索引（即位置索引 0, 1, 2, ..., max_len-1）映射到一个固定维度的向量（即位置编码向量）。`max_len` 是我们预期的最大序列长度（例如，对于 224x224 的图像，使用 16x16 的分块，会得到 196 个块，再加上一个 [CLS] token，总共 197），而向量的维度 `d_model` 必须与 patch embedding 的输出维度完全一致，这样才能进行后续的加法操作。

在数据流方面，这个模块本身**不直接接收嵌入序列作为输入**。它的职责是**生成**位置编码。真正的“加法”操作将在后续的 `PositionEncodingAdder` 模块中完成。因此，`LearnedPositionEncoding` 的输入是位置索引（通常由 `torch.arange` 生成），输出是对应的位置编码矩阵。这种设计遵循了“单一职责原则”，让每个组件的功能清晰、解耦，便于测试和复用。

关于设计选择，为什么不直接在 ViT 主干网络里硬编码这个逻辑？因为我们希望构建一个**模块化、可插拔**的系统。未来，你可能想在同一个项目中比较正弦编码和可学习编码的效果，或者尝试更复杂的二维相对位置编码。将位置编码逻辑封装成独立的、符合统一接口的类，可以让我们轻松地在不同方案之间切换，而无需修改主干网络的代码。这也是现代深度学习工程的最佳实践之一。

最后，我们来谈谈初始化。`nn.Embedding` 默认使用均匀分布进行初始化。对于位置编码，这种初始化通常是合适的，因为模型会在训练早期快速学习到有意义的位置关系。不过，在一些研究中（如 2024 年的一些 ViT 变体工作），也有人探索了使用正态分布或甚至用预训练的正弦编码来初始化可学习位置编码，以加速收敛。但在我们的基础实现中，采用默认初始化即可，保持简洁性和通用性。

#### 完整实现

```python
import torch
import torch.nn as nn

class LearnedPositionEncoding(nn.Module):
    """
    可学习位置编码模块。
    
    该模块通过一个可训练的嵌入层（nn.Embedding）为序列中的每个位置生成唯一的编码向量。
    这些向量在模型训练过程中会被优化，以捕获对特定任务最有用的位置信息。
    
    Attributes:
        position_embedding (nn.Embedding): 存储位置编码向量的嵌入层。
        
    Args:
        max_len (int): 序列的最大长度。例如，对于 ViT，这通常是 (H*W)/(P*P) + 1，
                      其中 H, W 是图像高宽，P 是分块大小，+1 是 [CLS] token。
        d_model (int): 嵌入向量的维度。必须与 patch embedding 的输出维度匹配。
        
    Example:
        >>> pos_encoder = LearnedPositionEncoding(max_len=197, d_model=768)
        >>> # 生成位置索引 [0, 1, 2, ..., 196]
        >>> position_ids = torch.arange(197).unsqueeze(0)  # shape: (1, 197)
        >>> pos_encoding = pos_encoder(position_ids)       # shape: (1, 197, 768)
    """
    
    def __init__(self, max_len: int, d_model: int):
        super(LearnedPositionEncoding, self).__init__()
        
        # 输入验证：确保参数合理
        if max_len <= 0:
            raise ValueError(f"'max_len' 必须是正整数，但得到了 {max_len}")
        if d_model <= 0:
            raise ValueError(f"'d_model' 必须是正整数，但得到了 {d_model}")
            
        # 创建嵌入层。num_embeddings 是词表大小（即位置数量），embedding_dim 是向量维度。
        # 这里的 'num_embeddings' 对应于序列的最大长度 'max_len'。
        self.position_embedding = nn.Embedding(
            num_embeddings=max_len,
            embedding_dim=d_model
        )
        
        # 注册一个缓冲区（buffer）来存储位置索引，方便后续使用。
        # 使用 register_buffer 而不是普通属性，这样它不会被视为模型参数，
        # 也不会在 optimizer.step() 中被更新，但会随模型一起保存/加载。
        self.register_buffer(
            'position_ids',
            torch.arange(max_len).unsqueeze(0)  # shape: (1, max_len)
        )
        
    def forward(self, position_ids: torch.Tensor = None) -> torch.Tensor:
        """
        前向传播，生成位置编码。
        
        如果未提供 position_ids，则使用内部注册的 position_ids 缓冲区。
        这使得调用更加灵活：既可以传入自定义的位置索引，也可以使用默认的连续索引。
        
        Args:
            position_ids (torch.Tensor, optional): 位置索引张量，shape 为 (batch_size, seq_len)。
                                                  如果为 None，则使用内部的 (1, max_len) 缓冲区。
                                                  默认为 None。
                                                  
        Returns:
            torch.Tensor: 位置编码张量，shape 为 (batch_size, seq_len, d_model)。
                          
        Raises:
            ValueError: 如果提供的 position_ids 超出了嵌入层的索引范围 [0, max_len)。
        """
        if position_ids is None:
            # 使用内部缓冲区。由于缓冲区是 (1, max_len)，而实际序列长度可能小于 max_len，
            # 我们需要根据实际输入序列长度进行切片。但在此基础实现中，
            # 我们假设调用者会传入正确的 position_ids 或已知序列长度。
            # 更健壮的做法是在 ViT 主干中处理，这里保持简单。
            position_ids = self.position_ids
        
        # 验证 position_ids 是否在有效范围内
        if position_ids.max() >= self.position_embedding.num_embeddings:
            raise ValueError(
                f"提供的 position_ids 最大值 ({position_ids.max().item()}) "
                f"超出了嵌入层的最大索引 ({self.position_embedding.num_embeddings - 1})。"
            )
            
        # 通过嵌入层查找对应的位置编码
        # input: (batch_size, seq_len) -> output: (batch_size, seq_len, d_model)
        position_encoding = self.position_embedding(position_ids)
        
        return position_encoding
```

#### 重要提示

- 【关键设计】本模块仅负责**生成**位置编码，不执行与 patch embedding 的相加操作。相加逻辑将在 `PositionEncodingAdder` 模块中实现，这种解耦设计提高了代码的模块化和可测试性。
- 【初始化与训练】`nn.Embedding` 的权重是随机初始化的，并在反向传播过程中与其他模型参数一同更新。这意味着位置编码会针对特定数据集和任务进行优化，这是其相对于固定编码的主要优势。
- 【序列长度处理】模块内部注册了一个从 0 到 `max_len-1` 的默认位置索引缓冲区。在实际 ViT 应用中，如果所有输入图像的分块数量固定（这是常见情况），可以直接使用此缓冲区。如果需要处理变长序列，则需在调用时传入动态生成的 `position_ids`。
- 【与正弦编码的对比】可学习编码在训练数据充足时通常表现更好，但缺乏外推能力（无法处理比 `max_len` 更长的序列）。而正弦编码具有良好的内插和外推性质。选择哪种方式取决于具体应用场景和数据规模。

### 3 PositionEncodingAdder

**文件**: `src/position_encoding_adder.py`

**目的**: 根据配置选择使用正弦余弦或可学习位置编码，并将其加到输入嵌入序列上，为后续Transformer块提供带有空间顺序信息的嵌入表示。

#### 详细说明

同学们好！在前两个步骤中，我们分别实现了两种主流的位置编码方式：`SinusoidalPositionEncoding`（固定、无需训练）和 `LearnedPositionEncoding`（可学习、需训练）。现在，我们需要一个统一的“调度器”——也就是本步骤要实现的 `PositionEncodingAdder` ——来根据用户配置动态选择其中一种，并将生成的位置编码**加到**来自图像分块嵌入模块（`PatchEmbedding`，即 step_1 的输出）的嵌入序列上。

为什么需要这样一个“加法融合器”？因为 Transformer 架构本身对输入序列的顺序是**完全无感**的。无论你把 token 按什么顺序排列，自注意力机制计算出的相关性都是一样的。但在视觉任务中，一个图像块在左上角还是右下角，意义天差地别！因此，我们必须在数据进入 Transformer 块之前，就将位置信息“烙印”到每个 token 的嵌入向量中。最简单也最有效的方式就是**逐元素相加**（element-wise addition），这也是原始 ViT 论文 [Dosovitskiy et al., ICLR 2021] 和后续绝大多数工作的标准做法。

我们的 `PositionEncodingAdder` 设计遵循了“策略模式”的思想。它不关心底层具体是哪种编码实现，只负责根据传入的 `encoding_type` 参数（'sinusoidal' 或 'learned'）来实例化对应的编码器，并确保其输出的形状与输入嵌入序列兼容。这里的关键在于**广播机制**（broadcasting）：位置编码通常是 `[1, sequence_length, embedding_dim]` 的形状，而输入嵌入是 `[batch_size, sequence_length, embedding_dim]`。PyTorch/TensorFlow 等框架会自动将位置编码沿 batch 维度广播，从而高效地完成加法操作。

在实现细节上，我们需要特别注意**序列长度的一致性**。位置编码的长度必须严格等于输入嵌入序列的长度（即 `num_patches + 1`，+1 是为了 class token）。如果用户配置的 `max_sequence_length` 小于实际输入长度，就必须抛出清晰的错误，避免静默的维度不匹配问题，这在调试时非常致命。此外，为了灵活性，我们将 `embedding_dim` 作为构造函数参数传入，这样同一个 `PositionEncodingAdder` 实例可以适配不同宽度的模型。

这个组件虽然代码量不大，但它是连接“静态图像块”和“动态注意力世界”的桥梁。没有它，ViT 就只是一个高级的词袋模型（Bag-of-Words），无法理解任何空间结构。通过这个统一接口，我们既能复现经典 ViT 的正弦编码，也能轻松实验更现代的可学习编码方案，比如 2024 年一些工作提出的相对位置编码变体（虽然本教程暂不涉及，但我们的设计为此预留了扩展性）。

最后，让我们展望下一步：一旦我们得到了这个“带位置信息的嵌入序列”，它就会被送入由多个 `TransformerBlock` 组成的编码器堆栈中。在那里，多头自注意力机制将开始工作，让每个图像块都能“看到”并“关注”到其他所有块，而位置编码则确保这种“关注”是有空间上下文的。可以说，`PositionEncodingAdder` 的输出质量，直接决定了后续注意力机制能否有效建模空间关系。

#### 完整实现

```python
import torch
import torch.nn as nn
from typing import Literal

# 假设这两个模块已在前序步骤中定义
from src.sinusoidal_position_encoding import SinusoidalPositionEncoding
from src.learned_position_encoding import LearnedPositionEncoding

class PositionEncodingAdder(nn.Module):
    """
    位置编码加法融合器。
    
    根据指定的类型（'sinusoidal' 或 'learned'），选择相应的位置编码策略，
    并将其加到输入的嵌入序列上，以注入空间位置信息。
    
    Args:
        encoding_type (Literal['sinusoidal', 'learned']): 位置编码的类型。
        embedding_dim (int): 嵌入向量的维度。
        max_sequence_length (int): 序列的最大长度（即最大图像块数 + 1，包含class token）。
        
    Attributes:
        position_encoder (nn.Module): 具体的位置编码实现模块。
        
    Input:
        x (torch.Tensor): 输入嵌入序列，形状为 [batch_size, sequence_length, embedding_dim]。
        
    Output:
        torch.Tensor: 添加了位置编码的嵌入序列，形状与输入相同。
        
    Example:
        >>> adder = PositionEncodingAdder('learned', embedding_dim=768, max_sequence_length=197)
        >>> x = torch.randn(4, 197, 768) # 4张图，每张图196个块+1个class token
        >>> output = adder(x)
        >>> print(output.shape) # torch.Size([4, 197, 768])
    """
    
    def __init__(
        self,
        encoding_type: Literal['sinusoidal', 'learned'],
        embedding_dim: int,
        max_sequence_length: int,
    ):
        super(PositionEncodingAdder, self).__init__()
        
        # 根据配置选择位置编码策略
        if encoding_type == 'sinusoidal':
            # 使用固定的正弦余弦位置编码
            self.position_encoder = SinusoidalPositionEncoding(
                embedding_dim=embedding_dim,
                max_sequence_length=max_sequence_length
            )
        elif encoding_type == 'learned':
            # 使用可学习的位置编码
            self.position_encoder = LearnedPositionEncoding(
                embedding_dim=embedding_dim,
                max_sequence_length=max_sequence_length
            )
        else:
            # 抛出明确的错误信息，指导用户正确配置
            raise ValueError(
                f"不支持的位置编码类型: '{encoding_type}'. "
                f"请选择 'sinusoidal' 或 'learned'."
            )
        
        # 保存配置参数，便于后续验证
        self.encoding_type = encoding_type
        self.embedding_dim = embedding_dim
        self.max_sequence_length = max_sequence_length

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播：将位置编码加到输入嵌入上。
        
        Args:
            x (torch.Tensor): 输入嵌入序列，形状应为 [batch_size, sequence_length, embedding_dim]。
            
        Returns:
            torch.Tensor: 添加了位置编码的嵌入序列。
            
        Raises:
            ValueError: 如果输入序列长度超过预设的最大长度。
        """
        batch_size, seq_len, embed_dim = x.shape
        
        # 验证输入维度是否匹配
        if embed_dim != self.embedding_dim:
            raise ValueError(
                f"输入嵌入维度 ({embed_dim}) 与位置编码器期望的维度 ({self.embedding_dim}) 不匹配。"
            )
            
        # 关键检查：确保序列长度不超过预设的最大长度
        if seq_len > self.max_sequence_length:
            raise ValueError(
                f"输入序列长度 ({seq_len}) 超过了位置编码器支持的最大长度 ({self.max_sequence_length})。\n"
                f"请在初始化 PositionEncodingAdder 时增大 'max_sequence_length' 参数，\n"
                f"或确保输入图像尺寸与模型配置一致。"
            )
        
        # 获取位置编码
        # position_encoding 的形状为 [1, max_sequence_length, embedding_dim]
        position_encoding = self.position_encoder()
        
        # 利用广播机制，将位置编码加到输入嵌入上
        # PyTorch 会自动将 [1, max_seq_len, dim] 广播到 [batch_size, seq_len, dim]
        # 注意：我们只取前 seq_len 个位置编码，以适应实际输入长度
        x_with_pos = x + position_encoding[:, :seq_len, :]
        
        return x_with_pos
```

#### 重要提示

- 【序列长度一致性至关重要】位置编码的最大长度 (`max_sequence_length`) 必须在初始化时根据模型架构（如图像分辨率、patch大小）预先确定。如果输入序列（例如，由于动态输入尺寸）超过了这个长度，必须显式报错，而不是静默截断或填充，否则会导致模型行为不可预测。这是ViT实现中最常见的错误来源之一。
- 【广播机制的高效性】代码中 `x + position_encoding[:, :seq_len, :]` 利用了PyTorch的广播机制。位置编码张量的第一个维度是1，因此它可以被高效地复制到整个batch，而无需实际的内存拷贝。这是一种既节省内存又提升计算效率的标准做法。
- 【设计的可扩展性】当前设计通过 `encoding_type` 参数实现了策略的灵活切换。未来如果要集成2024-2025年提出的更先进的位置编码方法（如条件位置编码CPE、旋转位置编码RoPE的视觉变体等），只需在此处添加新的 `elif` 分支并引入对应的模块即可，无需改动核心逻辑，体现了良好的软件工程实践。
- 【与Patch Embedding的契约】该模块严格依赖于 `PatchEmbedding` 模块的输出格式：`[batch_size, num_patches + 1, embedding_dim]`。其中 `+1` 对应于ViT中的class token。因此，在构建完整ViT模型时，必须确保 `max_sequence_length` 的设置包含了这个额外的token，通常为 `(H//P) * (W//P) + 1`，其中H/W是图像高宽，P是patch大小。

---

## 📦 依赖安装

### 所需依赖

- **torch (>=2.0.0)**: 核心深度学习框架，用于张量操作和模型构建
- **numpy (>=1.21.0)**: 用于数值计算和数组操作
- **PyYAML (>=6.0)**: 用于解析配置文件 config.yaml
- **pytest (>=7.0.0)**: 用于编写和运行单元测试

### 安装步骤

```bash
克隆本项目仓库
创建并激活一个新的 Python 虚拟环境 (推荐使用 conda 或 venv)
运行 `pip install -r requirements.txt` 安装所有依赖
进入 `src/` 目录开始学习和实现代码
```

---

## 🎮 使用教程

### 使用正弦余弦位置编码

**场景**: 当你希望模型具备处理比训练时更长序列的潜力，或者想减少可训练参数时。

```python
from src.sinusoidal_position_encoding import SinusoidalPositionEncoding
from src.position_encoding_adder import PositionEncodingAdder

# 假设 patch_embeddings 形状为 [batch_size, seq_len, embed_dim]
patch_embeddings = ...

# 创建正弦余弦编码器
pos_encoder = SinusoidalPositionEncoding(embed_dim=768, max_len=512)

# 创建加法器并应用
adder = PositionEncodingAdder(pos_encoder)
encoded_embeddings = adder(patch_embeddings)

print(encoded_embeddings.shape) # 应与输入 patch_embeddings 形状相同
```

**预期输出**: torch.Size([batch_size, seq_len, 768])

### 使用可学习位置编码

**场景**: 在标准 ViT 训练流程中，这是最常用的方式，尤其在有充足训练数据时。

```python
from src.learned_position_encoding import LearnedPositionEncoding
from src.position_encoding_adder import PositionEncodingAdder
import torch

# 假设 patch_embeddings 形状为 [batch_size, seq_len, embed_dim]
patch_embeddings = ...
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# 创建可学习编码器
pos_encoder = LearnedPositionEncoding(seq_len=197, embed_dim=768).to(device)

# 创建加法器并应用
adder = PositionEncodingAdder(pos_encoder)
encoded_embeddings = adder(patch_embeddings)

print(encoded_embeddings.shape) # 应与输入 patch_embeddings 形状相同
```

**预期输出**: torch.Size([batch_size, 197, 768])

---

## 📝 行动项

> [step_3] 实现位置编码 : 输入：嵌入序列（来自step_1）；输出：带有位置信息的嵌入序列。本步骤将实现可学习或正弦余弦形式的位置编码，并将其加到嵌入序列上，以保留空间顺序信息。该步骤不涉及注意力机制或Transformer块，仅负责添加位置信息，为后续模块提供有序输入。
