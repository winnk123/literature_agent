# Package 1: Vision Transformer 基础模块 — 图像分块嵌入实现

## 📋 概述

本教程包专注于 Vision Transformer (ViT) 架构的第一步核心组件：图像分块嵌入（Patch Embedding）。我们将学习如何将二维图像划分为固定大小的图像块（patches），并通过线性投影将其转换为一维嵌入向量序列，从而为后续的 Transformer 编码器提供输入。这是 ViT 区别于传统 CNN 的关键创新点之一，也是理解现代视觉 Transformer 的起点。通过本包，你将掌握从原始像素到序列化表示的完整映射过程，并为后续构建完整的 ViT 模型打下坚实基础。

## 📂 项目结构

```
package-01-patch-embedding/
├── README.md
├── requirements.txt
├── src/
│   └── patch_embedding.py
└── tests/
    └── test_patch_embedding.py
```

## 💡 理论基础

同学们好！今天我们来深入探讨 Vision Transformer 中一个看似简单却极其关键的步骤：**图像分块嵌入**（Patch Embedding）。为什么我们需要把图像切成小块？这背后其实蕴含着深度学习模型设计范式的重大转变——从“局部感受野 + 层层抽象”的卷积思维，转向“全局建模 + 序列处理”的 Transformer 思维。

在传统的卷积神经网络（CNN）中，模型通过小的卷积核在图像的局部区域滑动来提取特征。这种设计引入了一种称为**归纳偏置**（inductive bias）的先验假设：即图像的局部邻域包含重要信息，且空间结构具有平移不变性。这种归纳偏置对图像任务非常有效，但也限制了模型直接捕捉长距离依赖的能力。

Vision Transformer [Dosovitskiy et al., 2020] 提出了一种大胆的假设：如果我们能将图像视为一个“词序列”，那么自然语言处理中强大的 Transformer 架构是否也能直接用于视觉任务？要实现这一点，第一步就是将连续的二维图像离散化为一系列“视觉词元”（visual tokens）。这就是图像分块嵌入的核心动机。

具体来说，给定一张尺寸为 $H \times W \times C$ 的输入图像（其中 $H$ 和 $W$ 是高和宽，$C$ 是通道数，如 RGB 图像 $C=3$），我们将其均匀划分为 $N = \frac{H \times W}{P^2}$ 个不重叠的图像块，每个块的大小为 $P \times P \times C$。然后，我们将每个块**展平**（flatten）为一个长度为 $P^2C$ 的向量，称为**展平块向量**（Flattened Patch Vector）。这个中间表示将二维空间结构转换为一维向量，为后续的序列建模做准备：
$$\mathbf{x}_p \in \mathbb{R}^{P^2C}, \quad p = 1, 2, \dots, N$$

接着，我们通过一个**可学习的线性投影**（learnable linear projection）将每个展平块向量映射到一个 $D$ 维的嵌入空间。这个投影本质上是一个权重矩阵 $\mathbf{E} \in \mathbb{R}^{D \times P^2C}$，它通过矩阵乘法将输入向量变换到新的表示空间——就像用一把“可调节的尺子”把原始像素组合重新加权、压缩或扩展成更有语义的信息。这个过程可以表示为：
$$\mathbf{z}_p = \mathbf{E} \mathbf{x}_p \in \mathbb{R}^D$$

在实际实现中（如 PyTorch），这一操作通常由 `nn.Linear` 层完成，它就是一个全连接层，自动维护权重矩阵和偏置作为可学习参数。最终，一张图像被转换为一个包含 $N$ 个 $D$ 维嵌入向量的序列，形状为 $[N, D]$。当处理**批量数据**（batch）时（例如一次输入 $B$ 张图像，就像一次烤一盘饼干），输出形状变为 $[B, N, D]$，便于并行计算。

这一过程清晰地分为两个逻辑阶段：(1) **图像分块与展平**——将图像划分为固定大小的块并拉直；(2) **线性嵌入投影**——通过可学习的线性变换将每个块映射到统一的嵌入维度。这两个步骤共同构成了 Vision Transformer 的输入编码基础。

---

## 📖 核心概念详解

在开始实现之前，请先理解以下核心概念。这些概念是理解本包实现的关键前提。

### 图像分块（Image Patching）

想象一下，你有一幅巨大的壁画，但你只能通过一个个小窗户去观察它。每个窗户看到的是一小块画面，把这些小块拼起来，你就能还原整幅画。在 Vision Transformer 中，“图像分块”就是这个“开窗户”的过程。

具体来说，图像分块是指将一张完整的二维图像（比如 224×224 像素的 RGB 图像）切割成许多大小相同、互不重叠的小方块。这些小方块被称为“patches”。例如，如果我们将图像切成 16×16 像素的块，那么一张 224×224 的图像就会被分成 $(224/16) \times (224/16) = 14 \times 14 = 196$ 个 patches。

为什么要这样做？因为在原始的 Transformer 模型（最初用于自然语言处理）中，输入是一个“词序列”，比如“[我, 爱, 机器, 学习]”。每个词被转换成一个向量（词嵌入）。Vision Transformer 的核心思想是：能不能把图像也看作一个“视觉词序列”？每个“视觉词”就是一个图像块。这样，我们就可以直接套用强大的 Transformer 架构来处理图像了。

从数学上看，假设原始图像张量为 $\mathbf{X} \in \mathbb{R}^{H \times W \times C}$，其中 $H$ 是高度，$W$ 是宽度，$C$ 是通道数（如 RGB 为 3）。我们选择一个分块大小 $P$（通常 $P$ 能整除 $H$ 和 $W$），那么总共会有 $N = \frac{H \times W}{P^2}$ 个 patches。每个 patch 的尺寸是 $P \times P \times C$，我们可以将其展平（flatten）成一个长度为 $P^2C$ 的向量。这个过程不涉及任何参数，纯粹是数据重排。

需要注意的是，这种分块方式最早由 [Dosovitskiy et al., 2020] 在 Vision Transformer 论文中系统性地提出并验证，成为后续几乎所有 ViT 变体的基础。尽管看起来简单，但它成功地将视觉任务“翻译”成了序列建模问题，是跨模态思想的一次成功实践。近期工作如 [Liu et al., 2024] 也在探索动态分块或内容感知分块，但标准的均匀分块仍然是最主流、最高效的选择。

**为什么重要**: 图像是二维结构，而 Transformer 处理的是一维序列。图像分块是连接这两个世界的桥梁，没有这一步，就无法将图像输入到 Transformer 中。它是整个 ViT 架构的起点，决定了后续序列的长度和信息粒度。

**相关概念**: 序列化表示, 视觉词元（Visual Tokens）, 输入嵌入

**示例与类比**:

- 类比：就像把一本书的每一页切成相同大小的纸条，然后按顺序排列，形成一个新的“文本流”。
- 实际应用：在 ImageNet 分类任务中，224×224 的图像通常被切成 16×16 的块，得到 196 个 patches，再加上一个特殊的 [CLS] token，总序列长度为 197。

---

### 线性投影嵌入（Linear Projection Embedding）

当我们把图像切成小块后，每个块还是一个高维的像素向量（比如 16×16×3 = 768 维）。但 Transformer 通常在一个固定的、较低维度的空间（比如 768 维或 1024 维）中工作。这时，我们就需要一个“翻译官”——线性投影嵌入，把原始的像素块“翻译”成模型能理解的嵌入向量。

这个“翻译官”实际上就是一个全连接层（在 PyTorch 中就是 `nn.Linear`）。它的输入维度是 $P^2C$（即一个 patch 展平后的长度），输出维度是 $D$（即模型的隐藏维度，也叫嵌入维度）。这个全连接层的权重矩阵 $\mathbf{W} \in \mathbb{R}^{D \times P^2C}$ 是可学习的参数，在训练过程中会不断优化，以找到最佳的像素到嵌入的映射方式。

数学上，对于第 $i$ 个 patch 向量 $\mathbf{x}_i \in \mathbb{R}^{P^2C}$，其对应的嵌入向量 $\mathbf{z}_i \in \mathbb{R}^{D}$ 计算如下：
$$\mathbf{z}_i = \mathbf{W} \mathbf{x}_i + \mathbf{b}$$
其中 $\mathbf{b} \in \mathbb{R}^{D}$ 是偏置项。对所有 $N$ 个 patches 执行此操作后，我们就得到了一个嵌入序列 $\mathbf{Z} \in \mathbb{R}^{N \times D}$。

这个过程的关键在于：它不是简单的降维或升维，而是一种**语义映射**。模型通过学习这个线性变换，试图将具有相似视觉内容的图像块映射到嵌入空间中相近的位置。虽然形式上线性，但在与后续的非线性自注意力机制结合后，整体系统具备了强大的表达能力。

值得注意的是，[Dosovitskiy et al., 2020] 的原始 ViT 模型就采用了这种简单的线性投影。尽管后来有研究尝试用小型 CNN（如 3x3 卷积）代替线性层来提取更丰富的局部特征 [Xiao et al., 2021]，但线性投影因其简洁高效，仍然是 2024 年大多数 ViT 实现的首选 [Touvron et al., 2024]。它完美体现了“简单有效”的工程哲学。

**为什么重要**: 线性投影嵌入将原始像素块转换为统一维度的向量，使得不同图像可以产生相同长度的序列，同时也为模型提供了可学习的参数来适应下游任务。它是从原始数据到模型内部表示的关键转换步骤。

**相关概念**: 嵌入层（Embedding Layer）, 全连接层（Fully Connected Layer）, 特征映射

**示例与类比**:

- 类比：就像把不同语言的单词通过一本双语词典翻译成目标语言。这里的“词典”就是那个可学习的权重矩阵。
- 实际应用：在 ViT-Base 模型中，16x16x3=768 维的 patch 向量被线性投影到 768 维的嵌入空间，保持维度不变，便于后续处理。

---

## 🔧 实现步骤

### 1 PatchEmbedding

**文件**: `src/patch_embedding.py`

**目的**: 将输入的二维图像划分为固定大小的图像块，并通过线性层将每个图像块展平并映射为嵌入向量，形成序列化表示。

#### 详细说明

同学们好！今天我们正式开始构建 Vision Transformer（ViT）的第一块基石：**图像分块嵌入模块（Patch Embedding）**。在传统的卷积神经网络中，我们依赖局部感受野和层级结构来逐步提取特征；而 ViT 的核心思想是将整张图像视为一个“词序列”，从而直接应用自然语言处理中强大的 Transformer 架构。但图像本身是二维连续信号，如何将其转化为一维离散序列？这就是 Patch Embedding 要解决的问题。

具体来说，给定一张形状为 (B, C, H, W) 的图像（B 是 batch size，C 是通道数，H 和 W 是高和宽），我们需要将其划分为若干个非重叠的、固定大小 P×P 的图像块（patches）。例如，若输入是 224×224 的 RGB 图像（C=3），且 patch size P=16，则每张图会被划分为 (224/16) × (224/16) = 14×14 = 196 个 patch。每个 patch 的原始像素数据是一个 3×16×16 的张量，共 768 个数值。我们的目标是将这 768 维的向量通过一个可学习的线性变换，映射到一个 D 维的嵌入空间（如 D=768），从而得到一个长度为 N=196 的序列，每个元素都是 D 维向量——这正是 Transformer 所期望的输入格式。

那么，如何高效地实现这个“分块 + 投影”过程？一种直观的方法是使用 `torch.nn.Unfold` 或手动 reshape，但更简洁且计算高效的方式是使用 **1×1 卷积的变体——实际上，一个 stride=P、kernel_size=P 的卷积层，恰好能完成非重叠分块并同时进行线性投影**。这是因为：当卷积核大小等于 patch 大小且 stride 等于 patch 大小时，卷积操作等价于对每个 patch 独立进行线性变换。因此，我们可以用 `nn.Conv2d` 来实现整个 Patch Embedding 过程，这不仅代码简洁，而且能充分利用 GPU 的并行计算能力。

在我们的实现中，`PatchEmbedding` 类继承自 `nn.Module`，构造函数接收 `img_size`、`patch_size`、`in_channels` 和 `embed_dim` 四个关键参数。我们会先验证图像尺寸是否能被 patch size 整除（否则无法均匀分块），然后计算 patch 数量 N。接着，我们定义一个卷积层：`self.proj = nn.Conv2d(in_channels, embed_dim, kernel_size=patch_size, stride=patch_size)`。这个卷积层没有偏置（bias=False）是常见做法，因为后续通常会加上 LayerNorm，偏置可被吸收。前向传播时，输入 x 经过卷积后形状变为 (B, D, H/P, W/P)，我们再通过 `flatten(2).transpose(1, 2)` 将其转换为 (B, N, D) 的序列格式——这正是 Transformer 编码器的标准输入形状。

值得注意的是，这种设计完全符合 2024-2025 年视觉基础模型的最佳实践。例如，在最新的 ViT 变体如 ViT-22B（Google, 2024）和 EVA-02（BAAI, 2024）中，Patch Embedding 仍然是标准组件，尽管有些工作探索了重叠 patch 或多尺度 patch，但对于基础 ViT，非重叠固定大小 patch 仍是主流。此外，使用卷积实现而非显式 reshape + linear，不仅效率更高，也更容易与后续的混合架构（如 ConvNeXt + ViT）集成。

最后，我们考虑边界情况：如果输入图像尺寸不能被 patch size 整除怎么办？在本实现中，我们选择在初始化时抛出清晰的错误信息，强制用户确保输入尺寸合规。这比在运行时 silent failure 更安全。实际部署中，通常会在数据预处理阶段将图像 resize 到合适的尺寸（如 224×224），因此这一约束是合理的。

#### 完整实现

```python
import torch
import torch.nn as nn
from typing import Tuple

class PatchEmbedding(nn.Module):
    """
    图像分块嵌入模块（Patch Embedding）
    
    功能：将输入的二维图像划分为固定大小的非重叠图像块（patches），
         并通过可学习的线性投影将每个 patch 映射为嵌入向量，
         最终输出形状为 (B, N, D) 的序列，其中：
         - B: batch size
         - N: patch 数量 = (H * W) / (P * P)
         - D: 嵌入维度（embed_dim）
    
    参数:
        img_size (int): 输入图像的边长（假设为正方形，H=W=img_size）
        patch_size (int): 每个图像块的边长（P）
        in_channels (int): 输入图像的通道数（如 RGB 为 3）
        embed_dim (int): 嵌入向量的维度（D）
    
    输入形状:
        (B, C, H, W) -> 其中 H = W = img_size, C = in_channels
    
    输出形状:
        (B, N, D) -> 其中 N = (img_size // patch_size) ** 2
    
    示例:
        >>> model = PatchEmbedding(img_size=224, patch_size=16, in_channels=3, embed_dim=768)
        >>> x = torch.randn(2, 3, 224, 224)
        >>> out = model(x)
        >>> print(out.shape)  # torch.Size([2, 196, 768])
    """
    
    def __init__(
        self,
        img_size: int = 224,
        patch_size: int = 16,
        in_channels: int = 3,
        embed_dim: int = 768,
    ):
        super().__init__()
        
        # 验证图像尺寸是否能被 patch size 整除
        if img_size % patch_size != 0:
            raise ValueError(
                f"图像尺寸 {img_size} 不能被 patch size {patch_size} 整除。"
                f"请确保 img_size 是 patch_size 的整数倍。"
            )
        
        # 计算 patch 数量
        self.num_patches = (img_size // patch_size) ** 2
        self.patch_size = patch_size
        
        # 使用卷积层实现分块和线性投影
        # kernel_size=patch_size 且 stride=patch_size 的卷积等价于非重叠分块 + 线性变换
        self.proj = nn.Conv2d(
            in_channels=in_channels,
            out_channels=embed_dim,
            kernel_size=patch_size,
            stride=patch_size,
            bias=False  # 通常不使用偏置，因为后续有 LayerNorm
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播函数
        
        参数:
            x (torch.Tensor): 输入图像张量，形状为 (B, C, H, W)
        
        返回:
            torch.Tensor: 嵌入序列，形状为 (B, N, D)
        """
        # 获取输入形状
        B, C, H, W = x.shape
        
        # 验证输入尺寸是否匹配初始化时的 img_size
        # 注意：这里假设 H == W，且等于初始化时的 img_size
        if H != W:
            raise ValueError(f"输入图像必须是正方形，但得到 H={H}, W={W}")
        
        # 通过卷积层进行分块和投影
        # 输出形状: (B, embed_dim, H//patch_size, W//patch_size)
        x = self.proj(x)  # type: torch.Tensor
        
        # 将空间维度展平并转置为序列格式
        # flatten(2): 从第2维开始展平 -> (B, embed_dim, N)
        # transpose(1, 2): 交换 embed_dim 和 N 维度 -> (B, N, embed_dim)
        x = x.flatten(2).transpose(1, 2)
        
        return x
```

#### 重要提示

- 使用卷积层（Conv2d）而非显式的 reshape + Linear 层来实现 Patch Embedding 是当前（2024-2025）的最佳实践，因为它计算效率更高、代码更简洁，且能更好地利用硬件加速。卷积的 kernel_size 和 stride 同时设为 patch_size 时，天然实现了非重叠分块和线性投影的结合。
- 输入图像尺寸必须能被 patch_size 整除，这是 ViT 架构的基本约束。在实际应用中，通常在数据预处理阶段将图像 resize 到标准尺寸（如 224×224），因此该模块在初始化时进行严格校验，避免运行时错误。
- 输出的嵌入序列形状为 (B, N, D)，其中 N 是 patch 数量。这个序列将作为后续 Transformer 编码器的输入，因此必须确保 N 的计算正确。注意，这里没有包含 class token（[CLS]）或位置编码（positional embedding），这些将在后续模块中添加。
- 卷积层设置 bias=False 是常见做法，因为在 ViT 中，嵌入向量通常会立即经过 Layer Normalization，而 LayerNorm 会重新缩放和偏移，使得初始的偏置项变得冗余。这有助于减少参数数量并提高训练稳定性。

---

## 📦 依赖安装

### 所需依赖

- **torch (>=2.0.0)**: PyTorch 深度学习框架，用于构建和测试 Patch Embedding 模块
- **torchvision (>=0.15.0)**: 用于加载和预处理标准图像数据集（如 CIFAR10, ImageNet）进行测试
- **pytest (>=7.0.0)**: 用于编写和运行单元测试，确保模块功能正确

### 安装步骤

```bash
创建虚拟环境：`python -m venv vit-env`
激活虚拟环境：`source vit-env/bin/activate` (Linux/Mac) 或 `vit-env\Scripts\activate` (Windows)
安装依赖：`pip install -r requirements.txt`
运行测试验证安装：`pytest tests/`
```

---

## 🎮 使用教程

### 基本使用示例

**场景**: 创建一个 PatchEmbedding 模块，将 224x224 的 RGB 图像分块为 16x16 的 patches，并投影到 768 维嵌入空间

```python
from src.patch_embedding import PatchEmbedding
import torch

# 创建模块
patch_embed = PatchEmbedding(img_size=224, patch_size=16, in_channels=3, embed_dim=768)

# 创建一个 batch size 为 2 的随机图像
x = torch.randn(2, 3, 224, 224)

# 前向传播
embedded_patches = patch_embed(x)
print(embedded_patches.shape)  # 应输出 torch.Size([2, 196, 768])
```

**预期输出**: torch.Size([2, 196, 768])

### 不同分块大小测试

**场景**: 测试 32x32 分块大小，验证序列长度变化

```python
from src.patch_embedding import PatchEmbedding
import torch

patch_embed = PatchEmbedding(img_size=224, patch_size=32, in_channels=3, embed_dim=768)
x = torch.randn(1, 3, 224, 224)
embedded_patches = patch_embed(x)
print(embedded_patches.shape)  # 应输出 torch.Size([1, 49, 768]) 因为 (224/32)^2 = 7*7 = 49
```

**预期输出**: torch.Size([1, 49, 768])

---

## 📝 行动项

> [step_1] 实现图像分块嵌入 : 将输入图像划分为固定大小的图像块（patch），并通过线性投影将每个patch转换为嵌入向量。此步骤输出一个序列化的嵌入表示，作为后续模块的输入。
