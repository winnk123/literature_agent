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

#### Package 1: Package 1: Vision Transformer 图像分块嵌入模块实现

```bash
cd packages/01-package-1-vision-transformer-图像分块嵌入模块实现

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install torch==>=2.0.0 torchvision==>=0.15.0 numpy==>=1.21.0 ...

# 查看完整说明
cat README.md
```

#### Package 2: Package 2: Vision Transformer 多头自注意力机制实现

```bash
cd packages/02-package-2-vision-transformer-多头自注意力机制实现

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install torch==>=2.0.0 numpy==>=1.21.0 pytest==>=7.0.0

# 查看完整说明
cat README.md
```

#### Package 3: Package 3: Vision Transformer 位置编码模块实现

```bash
cd packages/03-package-3-vision-transformer-位置编码模块实现

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install torch==>=2.0.0 numpy==>=1.21.0 PyYAML==>=6.0 ...

# 查看完整说明
cat README.md
```

#### Package 4: Package 4: Vision Transformer 标准Transformer块实现

```bash
cd packages/04-package-4-vision-transformer-标准transformer块实现

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install torch==>=2.0.0 numpy==>=1.21.0

# 查看完整说明
cat README.md
```

#### Package 5: Package 5: Vision Transformer 完整网络结构整合与前向传播实现

```bash
cd packages/05-package-5-vision-transformer-完整网络结构整合与前向传播实现

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install torch==>=2.0.0 numpy==>=1.21.0

# 查看完整说明
cat README.md
```

## 🎯 基础使用示例

### Package 1 示例

用户希望使用默认参数（patch_size=16, embed_dim=768）处理一张 224x224 的 RGB 图像

```python
from src.patch_embedding import PatchEmbedding
import torch

# 创建模型实例
model = PatchEmbedding(img_size=224, patch_size=16, in_chans=3, embed_dim=768)

# 创建一个模拟的输入图像 (batch_size=1, channels=3, height=224, width=224)
x = torch.randn(1, 3, 224, 224)

# 前向传播
output = model(x)
print(f"输出形状: {output.shape}")  # 应该是 torch.Size([1, 196, 768])
```

详见: `packages/01-*/README.md`

### Package 2 示例

给定一个随机嵌入序列，计算其多头自注意力输出

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

详见: `packages/02-*/README.md`

### Package 3 示例

当你希望模型具备处理比训练时更长序列的潜力，或者想减少可训练参数时。

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

详见: `packages/03-*/README.md`

### Package 4 示例

使用随机初始化的嵌入序列作为输入，通过一个Transformer块进行处理

```python
import torch
from src.transformer_block import TransformerBlock

# 假设嵌入维度为768，序列长度为197（16x16图像分块+cls token）
embed_dim = 768
seq_len = 197
batch_size = 4

# 创建随机输入 (模拟来自step_3的带位置编码的嵌入)
x = torch.randn(batch_size, seq_len, embed_dim)

# 初始化Transformer块
transformer_block = TransformerBlock(embed_dim=embed_dim, num_heads=12, ff_dim=3072)

# 前向传播
output = transformer_block(x)
print(f"Input shape: {x.shape}")
print(f"Output shape: {output.shape}")
```

详见: `packages/04-*/README.md`

### Package 5 示例

创建一个小型ViT模型（用于CIFAR-10），输入随机图像张量，验证前向传播是否成功

```python
import torch
from src.vision_transformer import VisionTransformer

# 创建模型实例
model = VisionTransformer(
    img_size=32,
    patch_size=4,
    in_channels=3,
    num_classes=10,
    embed_dim=128,
    depth=4,
    num_heads=4,
    mlp_ratio=2.0
)

# 创建随机输入 (batch_size=2, channels=3, height=32, width=32)
x = torch.randn(2, 3, 32, 32)

# 前向传播
output = model(x)
print(f"Output shape: {output.shape}")  # 应为 [2, 10]
```

详见: `packages/05-*/README.md`

## 📚 进一步学习

- 查看每个包的 `README.md`
- 阅读 `FULL_TUTORIAL.md`
- 参考 `PROJECT_STRUCTURE.md`

## ❓ 获取帮助

如有问题，请查看文档或提交 issue。
