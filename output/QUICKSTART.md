# 🚀 快速开始指南

## 前置要求

- Python 3.8+
- pip 或 conda

## 安装步骤

### 1. 克隆或下载项目

```bash
git clone <repository-url>
cd research-implementation
```

### 2. 按顺序设置每个包

#### Package 1: Package 1: Vision Transformer 基础模块 — 图像分块嵌入实现

```bash
cd packages/01-package-1-vision-transformer-基础模块-图像分块嵌入实现

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install torch==>=2.0.0 torchvision==>=0.15.0 pytest==>=7.0.0

# 查看完整说明
cat README.md
```

#### Package 2: Package 2: Vision Transformer 中的位置编码机制实现

```bash
cd packages/02-package-2-vision-transformer-中的位置编码机制实现

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install torch==>=2.0.0 torchvision==>=0.15.0 pytest==>=7.0.0

# 查看完整说明
cat README.md
```

#### Package 3: Package 3: Vision Transformer 核心机制 — 多头自注意力模块实现

```bash
cd packages/03-package-3-vision-transformer-核心机制-多头自注意力模块实现

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install torch==>=2.0.0 numpy==>=1.21.0 pytest==>=7.0.0

# 查看完整说明
cat README.md
```

#### Package 4: Package 4: Vision Transformer 核心构建块 — Transformer 编码器层实现

```bash
cd packages/04-package-4-vision-transformer-核心构建块-transformer-编码器

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install torch==>=2.0.0 torchvision==>=0.15.0 pytest==>=7.0.0

# 查看完整说明
cat README.md
```

#### Package 5: Package 5: Vision Transformer 主干网络堆叠与完整模型构建

```bash
cd packages/05-package-5-vision-transformer-主干网络堆叠与完整模型构建

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install torch==>=2.0.0 torchvision==>=0.15.0 PyYAML==>=6.0

# 查看完整说明
cat README.md
```

## 🎯 基础使用示例

### Package 1 示例

创建一个 PatchEmbedding 模块，将 224x224 的 RGB 图像分块为 16x16 的 patches，并投影到 768 维嵌入空间

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

详见: `packages/01-*/README.md`

### Package 2 示例

初始化一个适用于 197 个图像块（14x14 + 1 cls token）、嵌入维度为 768 的位置编码模块。

```python
from src.positional_encoding import PositionalEncoding

# 创建可学习位置编码模块
pe = PositionalEncoding(embed_dim=768, max_patches=197, learnable=True)

# 假设我们有一个批次大小为 4 的嵌入张量
import torch
embeddings = torch.randn(4, 197, 768)

# 添加位置编码
output = pe(embeddings)
print(output.shape) # 应该输出 torch.Size([4, 197, 768])
```

详见: `packages/02-*/README.md`

### Package 3 示例

创建一个标准的多头自注意力模块并处理随机输入

```python
import torch
from src.multi_head_self_attention import MultiHeadSelfAttention

# 创建模块：嵌入维度768，头数12
mhsa = MultiHeadSelfAttention(embed_dim=768, num_heads=12)

# 模拟输入：batch_size=2, seq_len=197 (16x16 patches + cls token), embed_dim=768
x = torch.randn(2, 197, 768)

# 前向传播
output = mhsa(x)
print(f"Output shape: {output.shape}")  # 应该输出 torch.Size([2, 197, 768])
```

详见: `packages/03-*/README.md`

### Package 4 示例

创建一个标准的 ViT-Base 配置的编码器层，并对随机输入进行前向传播。

```python
import torch
from src.transformer_encoder_layer import TransformerEncoderLayer

# 设置参数
embed_dim = 768
num_heads = 12
ffn_hidden_dim = 3072

# 创建编码器层实例
encoder_layer = TransformerEncoderLayer(
    embed_dim=embed_dim,
    num_heads=num_heads,
    ffn_hidden_dim=ffn_hidden_dim
)

# 创建随机输入: [batch_size, seq_len, embed_dim]
x = torch.randn(2, 197, embed_dim)  # 197 = 1 ([CLS]) + 14*14 (patches)

# 前向传播
output = encoder_layer(x)
print(f"Input shape: {x.shape}")
print(f"Output shape: {output.shape}")
```

详见: `packages/04-*/README.md`

### Package 5 示例

快速验证模型是否能正确构建

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

详见: `packages/05-*/README.md`

## 📚 进一步学习

- 查看每个包的 `README.md`
- 阅读 `FULL_TUTORIAL.md`
- 参考 `PROJECT_STRUCTURE.md`

## ❓ 获取帮助

如有问题，请查看文档或提交 issue。
