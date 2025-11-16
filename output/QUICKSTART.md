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

#### Package 1: Package 1: 基于大语言模型引导的真实噪声图像数据准备与语义标注框架

```bash
cd packages/01-package-1-基于大语言模型引导的真实噪声图像数据准备与语义标注框架

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install openai==>=1.0.0 opencv-python==>=4.5.0 numpy==>=1.21.0 ...

# 查看完整说明
cat README.md
```

#### Package 2: Package 2: 基于视觉-语言模型与扩散机制的LLM引导去噪架构

```bash
cd packages/02-package-2-基于视觉-语言模型与扩散机制的llm引导去噪架构

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install torch==>=2.0.0 transformers==>=4.30.0 diffusers==>=0.20.0 ...

# 查看完整说明
cat README.md
```

#### Package 3: Package 3: 基于对比学习与多尺度自适应融合的扩散去噪模型训练与优化

```bash
cd packages/03-package-3-基于对比学习与多尺度自适应融合的扩散去噪模型训练与优化

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install torch==>=2.0.0 torchvision==>=0.15.0 transformers==>=4.30.0 ...

# 查看完整说明
cat README.md
```

#### Package 4: Package 4: 面向边缘设备的LLM引导扩散去噪模型压缩与部署优化

```bash
cd packages/04-package-4-面向边缘设备的llm引导扩散去噪模型压缩与部署优化

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install torch==>=2.0.0 torchvision==>=0.15.0 onnx==>=1.14.0 ...

# 查看完整说明
cat README.md
```

#### Package 5: Package 5: 基于多维指标与主观感知的LLM引导去噪模型综合评估体系

```bash
cd packages/05-package-5-基于多维指标与主观感知的llm引导去噪模型综合评估体系

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install torch==>=1.12.0 torchvision==>=0.13.0 lpips==>=0.1.4 ...

# 查看完整说明
cat README.md
```

## 🎯 基础使用示例

### Package 1 示例

用户提供一张真实含噪图像和对应的元数据描述，系统调用LLM生成结构化噪声标签。

```python
from src.llm_annotator import LLMAnnotator

# 初始化标注器
annotator = LLMAnnotator(api_key="your-api-key")

# 输入图像描述（模拟用户输入）
description = "使用Canon EOS R6在ISO 3200、1/60秒快门下拍摄的室内人像，面部有明显彩色噪点，背景细节模糊。"

# 生成标注
label = annotator.annotate(description)
print(label)
```

详见: `packages/01-*/README.md`

### Package 2 示例

用户有一张含噪声的风景照，希望用通用提示“清晰、自然、无噪”进行去噪。

```python
from src.main import LLMGuidedDenoiser
from PIL import Image

# 初始化去噪器
denoiser = LLMGuidedDenoiser(config_path="configs/denoising_config.yaml")

# 加载噪声图像
noisy_img = Image.open("data/sample_noisy_images/image_001.png")

# 使用默认提示去噪
clean_img = denoiser.denoise(
    image=noisy_img,
    prompt="清晰、自然、无噪",
    num_inference_steps=20
)

# 保存结果
clean_img.save("output_clean.png")
```

详见: `packages/02-*/README.md`

### Package 3 示例

用户希望使用提供的默认配置，在自定义数据集上训练一个基础的扩散去噪模型，仅使用MSE损失进行初步实验。

```python
import os
import yaml
from src.models.denoiser import DiffusionDenoiser
from src.data.dataloader import get_dataloaders
from src.utils.metrics import calculate_psnr_ssim

# 加载配置
config_path = 'configs/train_config.yaml'
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# 初始化数据加载器
train_loader, val_loader = get_dataloaders(
    data_dir='data',
    batch_size=config['training']['batch_size'],
    num_workers=4
)

# 初始化模型
model = DiffusionDenoiser(
    in_channels=3,
    model_chan...
```

详见: `packages/03-*/README.md`

### Package 4 示例

用户希望快速将已有的去噪模型转换为INT8格式，以便在支持ONNX Runtime的设备上部署，对延迟要求不高但希望显著减小模型体积。

```python
import torch
from src.compression.quantization import apply_ptq
from src.utils.config_loader import load_config

# 加载配置和预训练的FP32模型
config = load_config('configs/compression_config.yaml')
model_fp32 = torch.load('data/pretrained_teacher.pth')
model_fp32.eval()

# 准备校准数据加载器（此处简化，实际应使用DataLoader）
calibration_data = [...] # 从 ./data/calibration_set/ 加载的图像列表

# 应用训练后量化
model_int8 = apply_ptq(
    model=model_fp32,
    calibration_data=calibration_data,
    backend='onnx', # 指定后端为ONNX
    config=confi...
```

详见: `packages/04-*/README.md`

### Package 5 示例

对单个去噪模型的输出计算PSNR、SSIM和LPIPS，与原始干净图像对比。

```python
import os
from src.metrics.psnr_ssim import calculate_psnr_ssim
from src.metrics.lpips_metric import calculate_lpips
from src.utils.image_loader import load_image_pair

# 配置路径
clean_dir = "data/test_images/clean/"
denoised_dir = "data/test_images/denoised/model_z/"

psnr_list, ssim_list, lpips_list = [], [], []

for filename in os.listdir(clean_dir):
    clean_path = os.path.join(clean_dir, filename)
    denoised_path = os.path.join(denoised_dir, filename)
    
    clean_img, denoised_img = load...
```

详见: `packages/05-*/README.md`

## 📚 进一步学习

- 查看每个包的 `README.md`
- 阅读 `FULL_TUTORIAL.md`
- 参考 `PROJECT_STRUCTURE.md`

## ❓ 获取帮助

如有问题，请查看文档或提交 issue。
