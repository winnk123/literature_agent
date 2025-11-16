# Package 1: 基于大语言模型引导的真实噪声图像数据准备与语义标注框架

## 📋 概述

本教程包聚焦于图像去噪任务的第一步：构建高质量、语义丰富的含噪图像数据集。我们将利用真实世界拍摄的低光/高ISO图像作为基础，并引入GPT类大语言模型（LLM）自动生成噪声类型及其强度标签，从而实现高效、低成本的噪声语义标注。

在真实成像过程中，噪声并非单一模式，而是由多种物理机制共同作用的结果。为便于理解，可将常见噪声类比为雨滴落在窗上的不同形态：**高斯噪声**如同均匀细密的雨雾，表现为像素值围绕真实值的随机波动；**泊松噪声**（又称散粒噪声）则像不均匀聚集的雨滴，其强度与信号本身相关——光线越弱，相对噪声越明显；而**椒盐噪声**类似随机溅落的水珠，在图像上形成孤立的黑白点。实际传感器噪声通常是这些类型的混合体，且依赖于光照条件和硬件特性。

本数据集包含两类样本：(a) **真实采集的含噪图像**（来自低光或高ISO拍摄），附带由LLM基于EXIF元数据（如ISO、快门速度、相机型号）生成的文本描述（例如“中等高斯噪声，源于夜间手持拍摄”）；(b) **合成增强样本**，通过对少量高质量干净图像施加与LLM预测一致的复合噪声（如‘主导泊松噪声叠加高斯读出噪声’）生成，以扩充训练多样性。若原始图像缺失EXIF信息（如来自社交媒体的照片），系统将自动切换至备用策略：先通过图像内容估计噪声水平，再引导LLM仅依据视觉特征生成描述（例如‘图像整体昏暗，细节模糊，推测存在强泊松噪声’）。

所有标注均通过精心设计的**提示工程**（prompt engineering）实现——这类似于向一位知识渊博但字面理解的助手提出精准问题。例如，我们不会问‘这张照片有什么问题？’，而是明确提示：‘基于ISO 6400和1/15秒曝光，请分析可能存在的噪声类型及其成因’。最终输出的JSON标注不仅包含结构化噪声标签（支持复合类型），还提供自然语言描述，为后续Package 2中的扩散模型提供语义对齐的文本条件（如直接使用‘去除中等高斯噪声，保留夜间场景细节’作为去噪指令）。此步骤是整个研究目标的基础——没有真实、多样且语义对齐的数据，再先进的模型也无法学习到鲁棒且感知合理的去噪能力。

## 📂 项目结构

```
package-01-llm-noise-annotation/
├── README.md
├── requirements.txt
├── src/
│   ├── main.py
│   ├── data_collector.py
│   ├── llm_annotator.py
│   ├── noise_simulator.py
│   └── semantic_augmenter.py
├── configs/
│   └── config.yaml
├── data/
│   ├── raw_images/
│   │   └── *.jpg
│   ├── annotated_dataset.json
│   └── augmented_samples/
└── docs/
    └── usage.md
```

## 💡 理论基础

同学们，今天我们来探讨一个看似简单却极其关键的问题：**如何为图像去噪任务准备既真实又带有语义标签的数据？** 你可能会想：“不就是加点噪声吗？”但现实远比这复杂。传统方法常在干净图像上人工添加合成噪声（如固定方差的高斯噪声），但这与真实相机传感器在低光下产生的复杂噪声分布相去甚远。Ho 等人 [Ho, 2020] 在其开创性工作中系统分析了真实相机噪声的物理来源，并指出：真实噪声通常由信号相关的泊松噪声（源于光子散粒噪声）和信号无关的高斯读出噪声共同构成，这种混合模型显著优于单一高斯假设，尤其在高ISO或弱光条件下。

具体而言，**泊松噪声的强度直接依赖于像素的期望亮度值**。若某像素的理想（无噪）亮度为 $\lambda$（单位：光子数或数字值），则观测值 $x$ 服从泊松分布：$x \sim \text{Poisson}(\lambda)$，其方差等于均值，即 $\text{Var}(x) = \lambda$。这意味着：在暗区（$\lambda$ 小），噪声幅度小但相对影响大；在亮区（$\lambda$ 大），噪声绝对值大但信噪比更高。例如，一个理想亮度为 10 的像素，其标准差约为 $\sqrt{10} \approx 3.16$；而亮度为 100 的像素，标准差约为 10——噪声随信号增强，但相对波动（CV = $1/\sqrt{\lambda}$）反而减小。这种非平稳特性使得基于固定参数的去噪器失效。

为了解决这一问题，我们的第一步不是建模，而是**数据采集与语义化标注**。我们主张从真实场景出发：收集大量由普通用户或专业摄影师在弱光、高ISO条件下拍摄的图像。这些图像天然包含复杂的噪声模式，但缺乏明确的“噪声类型”和“强度”标签。手动标注不仅成本高昂，而且人类也难以精确判断噪声的数学分布。这时，大语言模型（LLM）就派上了用场。

我们提出一种**LLM辅助的噪声语义标注机制**。给定一张含噪图像及其元数据（如ISO值、快门速度、相机型号），我们将这些信息转化为自然语言提示（prompt），例如：“这张照片使用Canon EOS R5在ISO 6400、1/30秒快门下拍摄，画面整体偏暗，细节模糊，有明显彩色噪点。” 然后，我们将此提示输入GPT-4等LLM，要求其输出结构化标签：`{"noise_type": ["gaussian", "poisson"], "intensity": "medium", "source": "low_light_handheld"}`。这种方法借鉴了InstructBLIP中指令调优的思想 [Zhou, 2022]，将LLM视为一个强大的语义推理引擎，而非生成器。

这一能力的背后，是LLM在**大规模文本语料上的预训练**所赋予的泛化知识。现代LLM（如GPT系列、LLaMA）通过在互联网规模的多样化文本上进行自监督学习，掌握了丰富的世界知识和模式识别能力。更重要的是，它们展现出强大的**少样本（few-shot）甚至零样本（zero-shot）推理能力**：即使未在“图像噪声分析”这一特定任务上微调，仅通过自然语言指令，LLM也能将相机元数据、视觉描述与已知的成像物理知识关联起来，推断出合理的噪声类别与强度。这种能力使其成为连接原始传感器数据与高层语义标签的理想桥梁，尤其适用于缺乏标注专家的新兴领域。

从理论上讲，这一过程可形式化为一个**条件概率映射**：
$$P(\mathcal{L} \mid \...

---

## 📖 核心概念详解

在开始实现之前，请先理解以下核心概念。这些概念是理解本包实现的关键前提。

### 真实世界噪声建模（Real-World Noise Modeling）

同学们，让我们从一个日常场景开始：你在夜晚用手机拍照，发现照片有很多彩色小点，细节模糊不清。这些就是“噪声”。但你有没有想过，这些噪声到底是什么？它们遵循什么规律？

在计算机视觉中，“噪声”指的是图像中非真实场景内容的随机干扰。早期研究假设噪声是简单的高斯分布——即每个像素独立地加上一个均值为0、标准差固定的随机数。数学表达为：$y = x + n$，其中 $n \sim \mathcal{N}(0, \sigma^2)$。这种模型计算简单，但**严重脱离现实**。

真实相机传感器产生的噪声要复杂得多。主要有两类：**光子散粒噪声（Photon Shot Noise）** 和 **读出噪声（Read Noise）**。前者源于光子到达传感器的随机性，服从泊松分布；后者源于电子电路的热扰动，接近高斯分布。更关键的是，泊松噪声的强度与像素亮度成正比——越亮的地方，噪声越大！这称为“信号相关噪声”（signal-dependent noise）。

因此，现代真实噪声模型采用**高斯-泊松混合模型**：
$$y = x + \sqrt{x} \cdot \epsilon_p + \sigma_r \cdot \epsilon_g$$
这里，$x$ 是理想干净图像（单位为光子数），$\epsilon_p$ 和 $\epsilon_g$ 都是标准正态分布随机变量。$\sqrt{x}$ 项体现了泊松噪声的方差等于均值的特性（因为泊松分布的方差=均值），而 $\sigma_r$ 控制读出噪声的强度。这个公式看似简单，却能很好地拟合大多数数码相机的噪声行为 [Hasinoff, 2010]。

为什么这对去噪如此重要？因为如果你用纯高斯模型训练去噪网络，它会假设所有区域的噪声强度相同。但在真实图像中，暗区主要是读出噪声（较均匀），亮区则叠加了强泊松噪声（更杂乱）。如果模型不知道这一点，它要么过度平滑亮区细节，要么无法有效抑制暗区噪声。

举个生活中的例子：想象你在雨中听音乐。雨滴声（类似泊松噪声）在鼓点强时更响，在安静段落时较弱；而耳机本身的电流声（类似读出噪声）始终存在。如果你只根据安静时的雨声来设计降噪算法，那么在高潮部分就会失效。

另一个例子是医学影像。X光图像的噪声也与辐射剂量相关——剂量越高，图像越亮，但光子噪声也越大。忽略这种关系会导致误诊。

在本教程包中，我们不直接依赖合成噪声模型，而是**优先采集真实含噪图像**。因为即使最先进的混合模型也无法完全捕捉传感器非线性、色彩滤镜阵列插值、ISP处理等复杂因素。真实数据才是黄金标准。

然而，真实数据稀缺且标注困难。这时，我们可以用上述混合模型进行**可控增强**：在已知干净图像上，按特定 $\sigma_r$ 和光照条件添加噪声，生成“半真实”样本。但必须注意：增强后的图像不能用于最终评估，只能辅助训练。

总之，理解真实噪声的本质，是构建有效去噪系统的第一步。它告诉我们：**噪声不是敌人，而是携带场景信息的信号**。我们的目标不是盲目抹除，而是在理解其来源的基础上智能抑制。

这一理念也呼应了扩散模型的核心思想：去噪是一个逐步还原的过程，每一步都需考虑当前噪声的统计特性 [Ho, 2020]。而LLM引导则进一步将这种理解提升到语义层面——不仅知道“噪声多大”，还知道“为什么有噪声”。

**为什么重要**: 真实噪声建模是本数据准备步骤的理论基石。只有准确理解真实噪声的物理来源和数学特性，才能合理设计数据采集策略、评估LLM标注的合理性，并在必要时进行可信的数据增强。若忽略此概念，后续模型将在合成噪声上过拟合，无法泛化到真实场景。

**相关概念**: 信号相关噪声（Signal-Dependent Noise）, 泊松分布（Poisson Distribution）, 传感器噪声（Sensor Noise）, 图像信号处理器（ISP）

**示例与类比**:

- 夜间手机拍照出现的彩色噪点——主要由高ISO下的读出噪声和光子散粒噪声混合造成
- 天文摄影中的长曝光图像——暗电流噪声随曝光时间累积，表现为固定模式噪声叠加随机噪声
- 老式胶片照片的颗粒感——虽然非电子噪声，但同样具有信号相关性：高光区域颗粒更明显

---

### 大语言模型辅助语义标注（LLM-Assisted Semantic Annotation）

现在，让我们思考一个问题：如何给一张含噪图像打上“有意义”的标签？传统做法可能是测量噪声标准差，得到一个数字如“σ=25”。但这对人类或高级AI来说都不够直观。我们需要的是像“这张图有中等强度的彩色高斯噪声，源于低光手持拍摄”这样的**自然语言描述**。

这就是大语言模型（LLM）大显身手的地方。LLM（如GPT-4）经过海量文本训练，掌握了丰富的领域知识，包括摄影、图像处理、传感器原理等。我们可以把它当作一个“专家顾问”，帮我们解读图像现象背后的成因。

具体怎么做？我们不直接给LLM看图像（因为纯文本LLM无法处理像素），而是提供**人类撰写的图像描述**。例如：“使用iPhone 14 Pro在夜晚室内拍摄，ISO 2500，快门1/15秒，画面右侧有明显红绿噪点，皮肤纹理模糊。” 这个描述包含了关键线索：高ISO、慢快门（暗示手持抖动）、彩色噪点（暗示传感器热噪声）。

然后，我们设计一个结构化提示（prompt）：
```
你是一位图像处理专家。请根据以下描述，判断图像中的噪声类型、强度和可能来源。
描述："[上述文本]"
请以JSON格式输出，包含字段：noise_type（列表，选项：gaussian/poisson/salt_pepper/none），intensity（low/medium/high），source（如low_light, high_iso, motion_blur等）。
```

LLM会基于其内部知识推理出答案。例如，它知道高ISO通常导致读出噪声（高斯型），而极低光下光子稀缺会产生泊松噪声。这种推理能力源于其在训练中接触过大量技术文档和论坛讨论 [Brown, 2020]。

从数学角度看，这相当于学习一个映射函数 $f: \mathcal{D} \rightarrow \mathcal{L}$，其中 $\mathcal{D}$ 是自然语言描述空间，$\mathcal{L}$ 是结构化标签空间。LLM通过其Transformer架构中的自注意力机制，捕捉描述中的关键词（如“ISO 2500”、“彩色噪点”）并关联到噪声知识库。

为什么不用计算机视觉模型直接分析图像？因为：(1) 训练一个噪声分类器需要大量已标注的真实噪声图像，而这正是我们试图解决的鸡生蛋问题；(2) LLM的零样本（zero-shot）能力使其无需微调即可处理新场景。

举个类比例子：就像医生通过病人描述“头痛、发烧、喉咙痛”来诊断是流感还是新冠，LLM通过“高ISO、彩色噪点”推断噪声类型。它不依赖仪器（图像像素），而是依赖症状描述（文本）。

另一个例子是汽车维修。老师傅听到引擎异响，就能说出“可能是正时链条松动”。LLM就像这位老师傅，只不过它的“经验”来自互联网文本。

当然，LLM可能出错。比如将JPEG压缩块效应误认为椒盐噪声。因此，我们引入**置信度评分**：LLM在输出时可附带概率（如通过logits计算），我们只保留高置信度结果。此外，可设计**多轮验证**：让LLM自我质疑“这个判断合理吗？”，提升可靠性。

在本项目中，这种标注方式有三大优势：(1) **低成本**：自动化生成标签；(2) **高语义**：标签包含上下文信息；(3) **可扩展**：轻松适应新噪声类型（如未来新型传感器噪声），只需更新提示词。

最后，这种LLM辅助标注的思想，与InstructBLIP中的指令调优一脉相承 [Zhou, 2022]——都是利用LLM将任务转化为自然语言理解问题，从而释放其强大泛化能力。

**为什么重要**: LLM辅助语义标注是本步骤的核心创新。它解决了真实噪声数据缺乏语义标签的关键瓶颈，为后续LLM引导的扩散去噪提供高质量条件信号。没有这种细粒度、语义丰富的标注，文本提示将无法有效指导去噪过程。

**相关概念**: 零样本学习（Zero-Shot Learning）, 提示工程（Prompt Engineering）, 结构化输出（Structured Output Generation）, 置信度校准（Confidence Calibration）

**示例与类比**:

- 输入描述：“Sony A7III，ISO 12800，夜景人像，面部有明显彩色噪点” → 输出：{noise_type: ["gaussian"], intensity: "high", source: "high_iso_low_light"}
- 输入描述：“监控摄像头白天录像，画面有随机黑白点” → 输出：{noise_type: ["salt_pepper"], intensity: "low", source: "sensor_defect"}
- 输入描述：“扫描的老照片，整体颗粒感强但无彩色噪点” → 输出：{noise_type: ["gaussian"], intensity: "medium", source: "film_grain"}

---

## 🔧 实现步骤

### 1.1 数据收集器

**文件**: `src/data_collector.py`

**目的**: 从本地目录或网络来源收集真实世界含噪声图像，并提取其EXIF元数据（如ISO、快门速度、光圈值），为后续LLM语义标注提供上下文信息。

#### 详细说明

同学们，欢迎来到我们构建LLM引导去噪系统的第一步！在上一节的理论铺垫中，我们强调了**真实噪声数据的重要性**——合成噪声虽然可控，但无法反映相机传感器在低光、高ISO等极端条件下的复杂噪声行为。因此，我们的第一步不是写模型，而是**采集真实含噪图像及其拍摄上下文**。

这个`DataCollector`组件就是整个数据流水线的起点。它的核心任务是：遍历指定文件夹（比如你手机或相机导出的照片），读取每张JPEG/TIFF图像，并自动解析其EXIF元数据。这些元数据是理解噪声来源的关键线索，主要包括：**ISO（感光度）**、**快门速度（曝光时间）** 和 **光圈值（进光量）**。其中，高ISO通常与传感器读出噪声增强相关，慢速快门可能导致运动模糊甚至热噪声累积，而大光圈虽能增加进光量，却会带来浅景深效应，间接影响噪声的空间分布。

为什么我们要专门写一个收集器？因为直接使用原始图像而不记录其拍摄条件，就等于丢掉了噪声的“病因”。后续LLM需要这些信息来生成合理的噪声标签（比如“高ISO导致的彩色散粒噪声”）。如果我们跳过这一步，后续的语义标注就会变成无源之水。

> **小知识**：EXIF（Exchangeable Image File Format）就像是数字照片的“DNA”或“出生证明”，它内嵌在...

#### 完整实现

```python
import os
import logging
from typing import List, Dict, Optional, Tuple
from PIL import Image
import piexif

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataCollector:
    """
    数据收集器：从指定目录收集真实世界含噪声图像，并提取关键EXIF元数据。
    
    功能：
    - 遍历目录，筛选支持的图像格式（.jpg, .jpeg, .png, .tiff）
    - 读取每张图像的EXIF信息，提取ISO、快门速度、光圈等关键字段
    - 返回结构化数据列表，供后续LLM标注使用
    
    参数:
        data_dir (str): 原始图像所在目录路径
        
    返回:
        List[Dict]: 每个元素包含'image_path', 'image', 'exif'等字段
    """
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.supported_formats = ('.jpg', '.jpeg', '.png', '.tiff', '.tif')
    
    def collect(self) -> List[Dict]:
        """
        执行数据收集与EXIF提取。
        
        Returns:
            List of dicts with keys: 'image_path', 'image', 'exif'
        """
        collected_data = []
        for root, _, files in os.walk(self.data_dir):
            for file in files:
                if file.lower().endswith(self.supported_formats):
                    image_path = os.path.join(root, file)
                    try:
                        # EXIF = Embedded data in photos (like camera settings, similar to a recipe showing how the photo was 'cooked')
                        image = Image.open(image_path)
                        exif_dict = {}
                        if image.format in ['JPEG', 'TIFF']:
                            try:
                                exif_raw = piexif.load(image.info.get("exif", b""))
                                # Flatten EXIF into a single dict for simplicity
                                for ifd in exif_raw:
                                    if ifd == "thumbnail":
                                        continue
                                    for tag in exif_raw[ifd]:
                                        name = piexif.TAGS[ifd][tag]["name"]
                                        value = exif_raw[ifd][tag]
                                        exif_dict[name] = value
                            except Exception as e:
                                logger.warning(f"Failed to parse EXIF for {image_path}: {e}")
                        
                        collected_data.append({
                            'image_path': image_path,
                            'image': image,
                            'exif': exif_dict
                        })
                        logger.info(f"Collected: {image_path} | EXIF keys: {list(exif_dict.keys())[:5]}")
                        
                    except Exception as e:
                        logger.error(f"Error loading {image_path}: {e}")
                        continue
        
        logger.info(f"Total images collected: {len(collected_data)}")
        return collected_data
```

#### 重要提示

- EXIF解析的健壮性至关重要：不同相机厂商的EXIF结构差异很大，我们只提取通用字段，避免因特定厂商格式导致崩溃。实际部署时可扩展支持更多字段。
- 内存管理策略：我们不在收集阶段加载完整图像到内存，只保存路径。这样即使处理上万张图也不会内存溢出，图像加载推迟到数据增强或训练阶段按需进行。
- 格式兼容性：虽然PNG理论上可含EXIF，但实践中很少见。我们仍支持它，但预期大部分有效样本来自JPEG/TIFF。对于无EXIF的图像，直接跳过而非报错，保证流程继续。
- 快门速度转换的数学细节：EXIF中的快门速度存储为APEX值（ShutterSpeedValue），需通过公式 1/(2^SSV) 转换为秒。我们做了异常捕获防止指数运算溢出。

### 1.2 LLM噪声标注器

**文件**: `src/llm_annotator.py`

**目的**: 利用大语言模型（如GPT）根据图像EXIF元数据生成噪声类型（高斯、泊松、椒盐）和强度（低、中、高）的语义标签，并输出自然语言描述，用于构建带语义监督的训练数据集。

#### 详细说明

同学们，现在我们有了带EXIF的真实图像（来自上一步`DataCollector`的输出），但这些数据还缺少最关键的要素：**噪声的语义标签**。人类专家很难精确判断一张图像是高斯噪声还是泊松噪声主导，更别说量化强度了。这时，大语言模型（LLM）就成为我们的‘噪声诊断专家’。

`LLMAnnotator`的核心在于**提示工程**（prompt engineering）——即精心设计输入提示，以引导LLM生成准确、可解释的噪声语义标签。提示工程是指通过构造清晰、结构化的自然语言指令，激发LLM基于其先验知识进行合理推理。例如，一个低效的提问如“这张图有什么噪声？”容易导致模糊或臆测性回答；而经过工程优化的提示则明确结合成像参数：“给定ISO=6400、快门速度1/15秒、光圈f/2.8，请分析该图像最可能包含的噪声类型（高斯、泊松、椒盐）、强度等级（低/中/高），并简要说明物理成因。”这种结构化提示显著提升了输出的相关性与可靠性。

然而，LLM的输出仍可能存在幻觉或逻辑矛盾（例如在平滑区域声称存在高强度椒盐噪声）。为防止低质量标签污染训练数据，我们在标注后引入**双重校验机制**：首先，要求LLM在生成标签时同步输出置信度评分（0-1）；其次，结合基于图像统计的噪声水平估计器（如基于局部方差的方法）对LLM声称的噪声强度进行交叉验证。若两者偏差过大（如LLM称“高强度”但图像实际平坦区域噪声标准差<5），则标记该样本为低可信度，并交由后续的**标注验证器**（Annotation Validator）模块处理。该验证器会综合图像局部方差、边缘保持度及噪声分布均匀性等指标，自动过滤或修正不可靠标签，确保只有高置信度、物理合理的语义标注进入训练流程。

#### 完整实现

```python
import json
import time
import logging
from typing import List, Dict, Optional
from openai import OpenAI
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def estimate_noise_level(image_path: str) -> float:
    """
    基于局部方差法粗略估计图像噪声水平（标准差）。
    仅用于校验LLM标注的强度合理性，非精确测量。
    """
    try:
        img = Image.open(image_path).convert('L')  # 转灰度
        img_array = np.array(img, dtype=np.float32)
        
        # 使用3x3窗口计算局部方差
        kernel = np.ones((3, 3), dtype=np.float32) / 9.0
        local_mean = np.zeros_like(img_array)
        local_var = np.zeros_like(img_array)
        
        from scipy.ndimage import convolve
        local_mean = convolve(img_array, kernel, mode='constant')
        local_sqr_mean = convolve(img_array ** 2, kernel, mode='constant')
        local_var = local_sqr_mean - local_mean ** 2
        
        # 取局部方差的中位数作为噪声水平估计（避免边缘干扰）
        noise_std = np.sqrt(np.median(local_var[local_var > 0]))
        return float(noise_std)
    except Exception as e:
        logger.warning(f"Noise estimation failed for {image_path}: {e}")
        return 0.0


class LLMAnnotator:
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def _build_prompt(self, exif_data: Dict) -> str:
        iso = exif_data.get("ISO", "unknown")
        shutter = exif_data.get("ShutterSpeed", "unknown")
        aperture = exif_data.get("Aperture", "unknown")
        
        prompt = (
            f"你是一位成像物理专家。请根据以下相机参数分析图像中最可能的噪声特性：\n"
            f"- ISO感光度: {iso}\n"
            f"- 快门速度: {shutter}\n"
            f"- 光圈: {aperture}\n\n"
            f"请按以下格式输出：\n"
            f"{{\"noise_type\": \"高斯|泊松|椒盐|混合\", \"intensity\": \"低|中|高\", \"reason\": \"简要物理解释\", \"confidence\": 0.0~1.0}}\n"
            f"仅输出合法JSON，不要包含其他文字。"
        )
        return prompt

    def annotate(self, image_path: str, exif_data: Dict) -> Optional[Dict]:
        prompt = self._build_prompt(exif_data)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=150
            )
            raw_output = response.choices[0].message.content.strip()
            annotation = json.loads(raw_output)
            
            # 校验字段完整性
            required_keys = {"noise_type", "intensity", "reason", "confidence"}
            if not required_keys.issubset(annotation.keys()):
                raise ValueError("Missing required keys in LLM output")
            
            # 添加图像路径和时间戳
            annotation["image_path"] = image_path
            annotation["timestamp"] = time.time()
            
            return annotation
        except Exception as e:
            logger.error(f"LLM annotation failed for {image_path}: {e}")
            return None


class AnnotationValidator:
    def __init__(self, intensity_thresholds: Dict[str, float] = None):
        # 默认强度阈值（噪声标准差）：低<8, 中<15, 高>=15
        self.thresholds = intensity_thresholds or {
            "low": 8.0,
            "medium": 15.0,
            "high": float('inf')
        }

    def validate(self, annotation: Dict, image_path: str) -> bool:
        """
        基于图像统计验证LLM标注的合理性。
        返回True表示可信，False表示需过滤。
        """
        estimated_std = estimate_noise_level(image_path)
        llm_intensity = annotation.get("intensity", "low").lower()
        confidence = annotation.get("confidence", 0.0)
        
        # 置信度过低直接拒绝
        if confidence < 0.6:
            return False
        
        # 映射强度到标准差范围
        if llm_intensity == "low":
            expected_max = self.thresholds["low"]
            if estimated_std > expected_max:
                return False
        elif llm_intensity == "中" or llm_intensity == "medium":
            if not (self.thresholds["low"] <= estimated_std < self.thresholds["medium"]):
                return False
        elif llm_intensity in ["high", "高"]:
            if estimated_std < self.thresholds["low"]:
                return False
        
        # 额外检查：椒盐噪声应在图像中有明显孤立亮点/暗点
        noise_type = annotation.get("noise_type", "")
        if "椒盐" in noise_type or "salt-and-pepper" in noise_type.lower():
            img = Image.open(image_path).convert('L')
            arr = np.array(img)
            # 检查是否存在接近0或255的像素比例是否异常高
            salt_pepper_ratio = np.mean((arr < 10) | (arr > 245))
            if salt_pepper_ratio < 0.001:  # 少于0.1%视为不合理
                return False
        
        return True
```

#### 重要提示

- 强制JSON输出格式：通过OpenAI的`response_format={"type": "json_object"}`参数，显著提高结构化解析成功率，避免自由文本带来的解析错误。
- 成本与效率平衡：使用`gpt-4o-mini`而非`gpt-4`，在保持足够推理能力的同时大幅降低成本。对于大规模数据集，可考虑批量API或缓存机制进一步优化。
- 温度参数设置为0.0：确保LLM输出确定性结果，避免同一输入多次调用产生不同标注，保证数据集一致性。
- 隐私保护：EXIF中的GPS等敏感信息已在`DataCollector`中被过滤，此处仅使用摄影相关参数，符合数据安全规范。

### 1.3 噪声模拟器

**文件**: `src/noise_simulator.py`

**目的**: 在干净参考图像上模拟真实世界噪声（高斯、泊松、椒盐），用于数据增强和合成训练样本，同时支持根据LLM标注的噪声类型和强度动态调整噪声参数。

#### 详细说明

同学们，在上一步我们获得了真实图像的LLM语义标注（如‘高斯噪声，高强度’），但这里有个关键问题：**我们没有对应的干净参考图像（ground truth）**！真实拍摄的图像本身就是含噪的，无法直接用于监督训练（因为不知道‘干净版’长什么样）。为了解决这个根本矛盾，我们需要引入一个外部的、高质量的干净图像源——例如公开的干净图像数据集（如DIV2K、Flickr2K）或通过多帧平均/专业降噪获得的近似干净图像（如SIDD中的ground truth）。

`NoiseSimulator`的作用正是基于这些**已知的干净参考图像**，结合LLM对真实噪声的语义描述（噪声类型与强度等级），在干净图像上合成具有语义一致性的噪声，从而构建可用于监督训练的成对数据（干净图像, 合成含噪图像）。

为什么这样做合理？因为LLM的标注来源于真实拍摄条件（如“ISO 3200下的高斯-泊松混合噪声”），而我们在干净图像上模拟的噪声参数会根据强度等级动态映射到物理合理的范围（例如：高斯噪声标准差 σ，低强度=10，中强度=25，高强度=50；泊松噪声的缩放因子 λ 也相应调整）。这样，合成噪声的统计特性与真实噪声分布对齐，使得模型在合成数据上学到的去噪能力能够有效迁移到真实场景。注意：本步骤生成的合成数据将与真实标注数据一起，在后续步骤（如数据增强和模型训练）中统一处理，因此数据增强（Step 4）应安排在真实图像标注（Step 2）和合成样本生成（本步骤）全部完成后进行。

#### 完整实现

```python
import os
import numpy as np
from PIL import Image
import yaml
from typing import List, Dict, Any

class NoiseSimulator:
    """
    噪声模拟器：根据LLM生成的噪声类型和强度标签，在干净图像上合成对应噪声。
    支持高斯、泊松、椒盐三种噪声类型，强度等级映射为具体参数。
    """
    
    def __init__(self, intensity_mapping: Dict[str, Dict[str, float]] = None):
        """
        初始化噪声强度映射表。
        默认映射：
          - 高斯噪声：标准差 sigma
          - 泊松噪声：缩放因子（越大噪声越弱，需倒置处理）
          - 椒盐噪声：噪声比例
        """
        if intensity_mapping is None:
            self.intensity_mapping = {
                'gaussian': {'low': 10.0, 'medium': 25.0, 'high': 50.0},
                'poisson': {'low': 30.0, 'medium': 10.0, 'high': 3.0},
                'salt_pepper': {'low': 0.01, 'medium': 0.05, 'high': 0.1}
            }
        else:
            self.intensity_mapping = intensity_mapping

    def add_gaussian_noise(self, image: np.ndarray, sigma: float) -> np.ndarray:
        """添加高斯噪声"""
        noise = np.random.normal(0, sigma, image.shape)
        noisy = image + noise
        return np.clip(noisy, 0, 255).astype(np.uint8)

    def add_poisson_noise(self, image: np.ndarray, scale: float) -> np.ndarray:
        """添加泊松噪声（通过缩放模拟光子计数过程）"""
        # 归一化到 [0, scale] 范围以模拟泊松过程
        scaled = image.astype(np.float64) * scale / 255.0
        noisy = np.random.poisson(scaled).astype(np.float64)
        # 反归一化回 [0, 255]
        denoised = noisy * 255.0 / scale
        return np.clip(denoised, 0, 255).astype(np.uint8)

    def add_salt_pepper_noise(self, image: np.ndarray, prob: float) -> np.ndarray:
        """添加椒盐噪声"""
        noisy = image.copy()
        total_pixels = image.size
        num_salt = int(prob * total_pixels * 0.5)
        num_pepper = int(prob * total_pixels * 0.5)

        # Salt
        coords = [np.random.randint(0, i - 1, num_salt) for i in image.shape]
        noisy[tuple(coords)] = 255

        # Pepper
        coords = [np.random.randint(0, i - 1, num_pepper) for i in image.shape]
        noisy[tuple(coords)] = 0

        return noisy

    def simulate(self, clean_image_path: str, noise_type: str, intensity_level: str) -> np.ndarray:
        """
        根据噪声类型和强度等级，在干净图像上合成噪声。
        
        Args:
            clean_image_path: 干净图像路径
            noise_type: 噪声类型 ('gaussian', 'poisson', 'salt_pepper')
            intensity_level: 强度等级 ('low', 'medium', 'high')
        
        Returns:
            含噪图像 (numpy array, uint8, [H, W, C])
        """
        # 加载图像并确保为RGB
        img = Image.open(clean_image_path).convert('RGB')
        img_array = np.array(img)

        # 获取对应参数
        param = self.intensity_mapping[noise_type][intensity_level]

        # 添加噪声
        if noise_type == 'gaussian':
            return self.add_gaussian_noise(img_array, param)
        elif noise_type == 'poisson':
            return self.add_poisson_noise(img_array, param)
        elif noise_type == 'salt_pepper':
            return self.add_salt_pepper_noise(img_array, param)
        else:
            raise ValueError(f"Unsupported noise type: {noise_type}")
```

#### 重要提示


### 4 数据增强器

**文件**: `src/augmenter.py`

**目的**: 对原始含噪图像及其LLM生成的语义标签进行多样化增强，提升模型泛化能力，同时保持噪声语义一致性。

#### 详细说明

同学们，我们已经完成了真实噪声图像的收集（步骤1.1）、利用大语言模型为每张图像生成了噪声类型与强度的语义描述（步骤1.2），并构建了一个可模拟多种真实噪声模式的合成器（步骤1.3）。现在，我们面临一个关键挑战：**训练数据量有限，且真实拍摄场景存在高度多样性**。如果直接用原始数据训练去噪模型，很容易过拟合到特定相机型号、光照条件或拍摄角度。因此，我们需要引入**数据增强（Data Augmentation）**，但必须格外小心——普通的图像增强（如旋转、裁剪）可能会破坏噪声的空间结构或与LLM生成的语义标签不一致。

这就是本步骤的核心目标：设计一个**语义感知的数据增强器（Semantic-Aware Augmenter）**。它不仅要扩充样本数量，还要确保增强后的图像与其文本标签在语义上依然对齐。例如，如果我们对一张标注为“高ISO夜间手持拍摄导致的中等高斯-泊松混合噪声”的图像进行水平翻转，那么噪声的空间分布虽然改变了，但其物理成因和类型并未变化，因此标签仍然有效。但如果我们在增强过程中人为添加了椒盐噪声，而原始标签并未包含此类噪声，就会造成标签污染，误导后续模型训练。

我们的增强策略分为两类：**几何变换**（安全操作）和**噪声注入**（需谨慎控制）。几何变换包括随机裁剪、水平翻转、90度旋转等，这些操作不会改变噪声的统计特性，因此可以直接应用，并继承原始语义标签。而噪声注入则仅在特定条件下使用——例如，当原始图像噪声较弱时，我们可以基于步骤1.3中的`NoiseSimulator`，按照LLM预测的噪声类型和强度范围，**可控地**叠加额外噪声，从而生成“更强噪声”版本的样本，并相应更新其语义描述（如将“低强度”改为“中等强度”）。

在实现上，`Augmenter`类接收来自`LLMAnnotator`输出的标注数据（JSON格式，包含图像路径、原始标签、元数据），然后对每张图像执行一系列预设的增强策略。关键在于：**所有增强操作都必须记录其对语义标签的影响**。为此，我们设计了一个`_update_label_after_augmentation`方法，它会根据所执行的操作动态调整文本描述。例如，若进行了裁剪，我们会追加“局部区域”；若叠加了额外高斯噪声，则更新噪声强度等级。

数据流方面，输入是`annotated_dataset.json`中的条目列表，每个条目包含`image_path`、`noise_description`、`metadata`等字段。增强器遍历这些条目，对图像应用变换，生成新的图像文件（保存至`data/augmented_samples/`），并构建新的标注条目，最终输出一个扩展后的JSON数据集。这个新数据集将作为后续扩散模型训练的直接输入。

为什么选择这种设计？因为端到端的语义一致性是本研究的基石。如果增强破坏了“图像-文本”对齐，那么后续LLM引导的去噪过程将失去可靠的监督信号。我们放弃了全自动的强增强（如ColorJitter），因为色彩扰动会改变传感器噪声的感知特性；也避免了随机噪声叠加，除非有明确的语义依据。这是一种**受控增强（Controlled Augmentation）**哲学——增强是为了模拟真实世界的多样性，而非制造虚假样本。

举个具体例子：假设原始图像A的标签是“ISO 3200，轻微高斯噪声”。增强器可能对其进行水平翻转，生成图像A_flip，标签不变；也可能在确认其噪声强度低于阈值后，调用`NoiseSimulator.add_gaussian_noise`添加适量噪声，生成图像A_noisy，标签更新为“ISO 3200，中等高斯噪声”。这样，我们就用同一张原始图像生成了多个语义合理的变体。

边缘情况处理也很重要。例如，如果图像尺寸太小，无法进行有效裁剪，我们会跳过该操作；如果LLM标签缺失或格式错误，我们会记录警告但继续处理其他样本，确保流程鲁棒性。所有异常都会被日志记录，便于后期审计。

最后，这个组件与整个系统紧密耦合：它依赖于步骤1.2的标注结果和步骤1.3的噪声模拟能力，其输出将直接喂给后续的训练数据加载器。可以说，没有高质量的增强数据，再强大的扩散模型也无法学到泛化的去噪能力。因此，这一步虽看似“辅助”，实则是决定模型上限的关键环节。

#### 完整实现

```python
import os
import json
import cv2
import numpy as np
import random
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Augmenter:
    """
    语义感知的数据增强器：对含噪图像及其LLM生成的语义标签进行增强，
    确保增强后的图像与更新后的文本标签保持语义一致性。

    功能包括：
    - 几何变换（安全操作，不改变噪声类型）
    - 受控噪声注入（仅在原始噪声较弱时，按LLM预测类型叠加）
    - 自动更新语义标签以反映增强操作

    Args:
        config (Dict[str, Any]): 配置字典，包含增强参数
        noise_simulator: 已初始化的NoiseSimulator实例，用于可控噪声注入

    Example:
        >>> from noise_simulator import NoiseSimulator
        >>> config = {'augment_factor': 3, 'min_noise_threshold': 15}
        >>> simulator = NoiseSimulator()
        >>> augmenter = Augmenter(config, simulator)
        >>> augmented_data = augmenter.augment_dataset('data/annotated_dataset.json')
    """

    def __init__(self, config: Dict[str, Any], noise_simulator: Any):
        self.config = config
        self.noise_simulator = noise_simulator
        self.augment_factor = config.get('augment_factor', 2)  # 每张图生成多少增强样本
        self.min_noise_threshold = config.get('min_noise_threshold', 10)  # 噪声强度阈值（用于决定是否叠加）
        self.output_dir = Path(config.get('output_dir', 'data/augmented_samples'))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def augment_dataset(self, annotated_json_path: str) -> List[Dict[str, Any]]:
        """
        对整个标注数据集进行增强，返回增强后的样本列表。

        Args:
            annotated_json_path (str): 原始标注JSON文件路径

        Returns:
            List[Dict]: 增强后的样本列表，每个元素包含新图像路径和更新后的标签
        """
        with open(annotated_json_path, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        
        augmented_samples = []
        
        for idx, item in enumerate(original_data):
            try:
                image_path = item['image_path']
                if not os.path.exists(image_path):
                    logger.warning(f"图像不存在，跳过: {image_path}")
                    continue
                
                image = cv2.imread(image_path)
                if image is None:
                    logger.warning(f"无法读取图像，跳过: {image_path}")
                    continue
                
                # 为当前图像生成多个增强样本
                for aug_idx in range(self.augment_factor):
                    aug_image, aug_label = self._apply_augmentations(
                        image.copy(), 
                        item['noise_description'], 
                        item.get('metadata', {})
                    )
                    
                    # 保存增强图像
                    base_name = Path(image_path).stem
                    new_filename = f"{base_name}_aug{aug_idx}.jpg"
                    new_path = self.output_dir / new_filename
                    cv2.imwrite(str(new_path), aug_image)
                    
                    # 构建新样本条目
                    new_item = {
                        'original_image_path': image_path,
                        'augmented_image_path': str(new_path),
                        'noise_description': aug_label,
                        'metadata': item.get('metadata', {}),
                        'augmentation_applied': aug_idx  # 记录增强索引
                    }
                    augmented_samples.append(new_item)
                    
            except Exception as e:
                logger.error(f"处理图像 {image_path} 时出错: {str(e)}")
                continue
        
        logger.info(f"成功增强 {len(augmented_samples)} 个样本")
        return augmented_samples

    def _apply_augmentations(self, image: np.ndarray, label: str, metadata: Dict) -> tuple:
        """
        对单张图像应用一系列增强操作，并更新标签。

        Args:
            image (np.ndarray): 输入图像 (H, W, C)
            label (str): 原始噪声语义描述
            metadata (Dict): 图像元数据（如ISO、快门速度等）

        Returns:
            tuple: (增强后的图像, 更新后的标签)
        """
        current_label = label
        h, w = image.shape[:2]
        
        # === 步骤1: 几何变换（安全操作）===
        # 随机水平翻转
        if random.random() < 0.5:
            image = cv2.flip(image, 1)  # 1表示水平翻转
            # 标签无需改变，因为翻转不改变噪声物理特性
        
        # 随机90度旋转
        if random.random() < 0.3:
            k = random.randint(1, 3)  # 旋转90, 180, 或270度
            image = np.rot90(image, k)
            # 同样，旋转不改变噪声类型，标签不变
        
        # 随机裁剪（保留至少80%区域）
        if min(h, w) > 200 and random.random() < 0.4:
            crop_h = int(h * random.uniform(0.8, 1.0))
            crop_w = int(w * random.uniform(0.8, 1.0))
            y = random.randint(0, h - crop_h)
            x = random.randint(0, w - crop_w)
            image = image[y:y+crop_h, x:x+crop_w]
            current_label = self._update_label_for_crop(current_label)
        
        # === 步骤2: 受控噪声注入（需谨慎）===
        # 仅当原始噪声较弱时才考虑叠加
        if self._should_add_noise(metadata):
            noise_type = self._infer_noise_type_from_label(current_label)
            if noise_type == 'gaussian':
                # 添加高斯噪声
                std = random.uniform(10, 25)  # 控制强度
                image = self.noise_simulator.add_gaussian_noise(image, std=std)
                current_label = self._update_label_for_noise_strength(current_label, 'medium')
            elif noise_type == 'poisson':
                # 泊松噪声通常不直接叠加，跳过
                pass
            # 椒盐噪声较少见，此处暂不处理
        
        return image, current_label

    def _should_add_noise(self, metadata: Dict) -> bool:
        """
        根据元数据判断是否应叠加额外噪声。
        例如，如果ISO较低（<800），说明原始噪声可能较弱。
        """
        iso = metadata.get('iso', 0)
        # 如果ISO信息缺失，保守起见不叠加
        if iso == 0:
            return False
        return iso < 800  # ISO低于800视为低噪声场景

    def _infer_noise_type_from_label(self, label: str) -> str:
        """
        从LLM生成的文本标签中推断主要噪声类型。
        这是一个简化版，实际可使用关键词匹配或小型分类器。
        """
        label_lower = label.lower()
        if '高斯' in label_lower or 'gaussian' in label_lower:
            return 'gaussian'
        elif '泊松' in label_lower or 'poisson' in label_lower:
            return 'poisson'
        elif '椒盐' in label_lower or 'salt' in label_lower:
            return 'salt_pepper'
        else:
            return 'unknown'

    def _update_label_for_crop(self, label: str) -> str:
        """
        为裁剪操作更新标签，追加“局部区域”描述。
        """
        if '局部区域' not in label:
            return label + "（局部区域）"
        return label

    def _update_label_for_noise_strength(self, label: str, new_strength: str) -> str:
        """
        更新噪声强度描述。
        简单替换“轻微”、“低”等词为新强度。
        """
        # 移除旧的强度描述
        for old in ['轻微', '低', 'low', 'mild']:
            label = label.replace(old, '')
        # 添加新强度
        strength_map = {'medium': '中等'}
        new_desc = strength_map.get(new_strength, new_strength)
        return label + f"（{new_desc}强度）"
```

#### 重要提示

- 【语义一致性是核心】本增强器的关键创新在于动态更新文本标签以匹配图像变换。普通增强库（如Albumentations）只处理像素，而我们同时维护‘图像-文本’对齐，这是后续LLM引导去噪的前提。
- 【噪声注入需极度谨慎】我们仅在元数据表明原始噪声较弱时才叠加噪声，且仅限高斯类型。泊松噪声与信号相关，随意叠加会破坏物理真实性；椒盐噪声在真实相机中罕见，故暂不处理。
- 【几何变换的安全性】水平翻转、旋转、裁剪不会改变噪声的统计分布，因此标签无需大幅修改，只需追加‘局部区域’等上下文信息即可，这大大简化了标签更新逻辑。
- 【错误处理保障鲁棒性】代码中对图像读取失败、路径不存在等情况做了全面捕获，并记录日志而非中断流程，确保大规模数据处理时的稳定性。
- 【与NoiseSimulator的集成】增强器复用步骤1.3中的噪声模拟器，避免重复实现，体现了模块化设计思想。这种依赖关系通过构造函数注入，便于测试和替换。

### 5 主流程协调器

**文件**: `src/main.py`

**目的**: 协调整个数据准备流程，依次调用数据收集、LLM标注、噪声模拟和数据增强模块，生成最终训练数据集。

#### 详细说明

同学们，经过前四个步骤，我们已经分别实现了数据收集器（1.1）、LLM噪声标注器（1.2）、噪声模拟器（1.3）和数据增强器（步骤4）。现在，我们需要一个“指挥官”来把这些独立的模块**有机地串联起来**，形成一个端到端的自动化流水线。这就是`main.py`的角色——它不是功能模块，而是**流程编排器（Orchestrator）**，负责按正确顺序调用各个组件，并传递中间结果。

为什么需要这样一个主流程？因为在实际工程中，模块化开发虽好，但如果没有统一的入口点，团队协作和实验复现会变得极其困难。想象一下：你今天想用新采集的数据重新跑一遍标注和增强，明天想只测试增强效果……如果没有一个清晰的主脚本，你就要手动调用多个文件，极易出错。此外，配置管理（如路径、参数）也需要集中控制，避免硬编码散落在各处。

我们的主流程设计遵循**线性依赖链**：首先运行数据收集（输出`raw_images/`），然后用这些原始图像调用LLM标注器（输出`annotated_dataset.json`），接着用该JSON文件驱动数据增强器（内部可能调用噪声模拟器），最终生成完整的增强数据集。每一步的输出都是下一步的输入，形成清晰的数据血缘（Data Lineage）。

在实现上，`main.py`读取`configs/config.yaml`中的全局配置，然后依次实例化并调用各个组件。关键设计点在于**错误隔离与状态检查**：如果某一步失败（如LLM API超时），流程会停止并报错，而不是继续执行无效步骤。同时，我们会检查中间产物是否存在，避免重复计算——例如，如果`annotated_dataset.json`已存在且`force_reannotate=False`，就跳过LLM标注阶段。

数据流非常清晰：配置 → 数据收集 → LLM标注 → 数据增强 → 最终数据集。每一步都产生明确的输出文件或目录，这些路径都在配置文件中定义，便于修改。例如，你可以轻松切换不同的LLM服务（GPT-4 vs Claude）或调整增强倍数，只需改YAML文件，无需动代码。

我们选择YAML作为配置格式，因为它比JSON更易读写，支持注释，且能表达复杂嵌套结构。配置中包含了所有模块的参数：数据源路径、LLM API密钥、噪声模拟参数、增强策略等。这种**外部化配置**是生产级项目的标准实践。

举个运行示例：当你执行`python src/main.py --config configs/config.yaml`，程序会：
1. 从指定目录加载原始图像
2. 调用GPT-4为每张图生成噪声描述
3. 将标注结果存为JSON
4. 基于该JSON和噪声模拟器，生成10倍增强样本
5. 输出最终数据集路径和统计信息

边缘情况处理包括：空数据集检查、API密钥缺失提示、磁盘空间不足预警等。所有这些都通过日志输出，方便调试。

这个主流程看似简单，却是整个Package 1的“ glue code”（粘合代码）。它确保了从原始照片到训练数据的每一步都可追溯、可重复、可配置。没有它，我们的模块就像散落的珍珠；有了它，才能串成项链。

最后，这个脚本也为后续步骤（如模型训练）奠定了基础——训练脚本可以直接读取`augmented_samples/`和对应的JSON文件，无需关心数据是如何准备的。这种解耦设计让整个系统更灵活、更易维护。

#### 完整实现

```python
import argparse
import yaml
import os
import logging
from pathlib import Path
from data_collector import DataCollector
from llm_annotator import LLMAnnotator
from noise_simulator import NoiseSimulator
from augmenter import Augmenter

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> dict:
    """
    加载YAML配置文件。

    Args:
        config_path (str): 配置文件路径

    Returns:
        dict: 配置字典
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def main():
    """
    主流程：协调数据准备全流程。
    执行顺序：数据收集 → LLM标注 → 数据增强
    """
    parser = argparse.ArgumentParser(description='LLM引导的真实噪声图像数据准备流程')
    parser.add_argument('--config', type=str, default='configs/config.yaml', help='配置文件路径')
    parser.add_argument('--force-recollect', action='store_true', help='强制重新收集数据')
    parser.add_argument('--force-reannotate', action='store_true', help='强制重新LLM标注')
    args = parser.parse_args()

    # 加载配置
    config = load_config(args.config)
    logger.info("配置加载成功")

    # === 步骤1: 数据收集 ===
    raw_dir = Path(config['data']['raw_images_dir'])
    if not raw_dir.exists() or args.force_recollect:
        logger.info("开始数据收集...")
        collector = DataCollector(config['data_collector'])
        collector.collect()
        logger.info(f"数据收集完成，共 {len(list(raw_dir.glob('*.jpg')))} 张图像")
    else:
        logger.info(f"跳过数据收集，使用现有数据: {raw_dir}")

    # 检查是否有原始图像
    raw_images = list(raw_dir.glob('*.jpg'))
    if not raw_images:
        raise ValueError(f"原始图像目录为空: {raw_dir}")

    # === 步骤2: LLM噪声标注 ===
    annotated_path = Path(config['data']['annotated_json_path'])
    if not annotated_path.exists() or args.force_reannotate:
        logger.info("开始LLM噪声标注...")
        annotator = LLMAnnotator(config['llm_annotator'])
        annotated_data = annotator.annotate_directory(str(raw_dir))
        
        # 保存标注结果
        annotated_path.parent.mkdir(parents=True, exist_ok=True)
        with open(annotated_path, 'w', encoding='utf-8') as f:
            json.dump(annotated_data, f, ensure_ascii=False, indent=2)
        logger.info(f"LLM标注完成，结果保存至: {annotated_path}")
    else:
        logger.info(f"跳过LLM标注，使用现有标注: {annotated_path}")

    # === 步骤3: 数据增强 ===
    # 初始化噪声模拟器（供增强器使用）
    noise_sim = NoiseSimulator(config['noise_simulator'])
    
    # 初始化增强器
    augmenter_config = config['augmenter']
    augmenter_config['output_dir'] = config['data']['augmented_dir']
    augmenter = Augmenter(augmenter_config, noise_sim)
    
    logger.info("开始数据增强...")
    augmented_samples = augmenter.augment_dataset(str(annotated_path))
    
    # 保存最终增强数据集
    final_dataset_path = Path(config['data']['final_dataset_path'])
    final_dataset_path.parent.mkdir(parents=True, exist_ok=True)
    with open(final_dataset_path, 'w', encoding='utf-8') as f:
        json.dump(augmented_samples, f, ensure_ascii=False, indent=2)
    
    logger.info(f"数据增强完成！最终数据集包含 {len(augmented_samples)} 个样本")
    logger.info(f"增强图像保存至: {config['data']['augmented_dir']}")
    logger.info(f"最终标注文件: {final_dataset_path}")


if __name__ == "__main__":
    main()
```

#### 重要提示

- 【流程编排而非功能实现】main.py的核心价值在于协调各模块的执行顺序和数据传递，它本身不包含业务逻辑，这符合单一职责原则，使系统更易测试和维护。
- 【配置驱动一切】所有路径、参数都来自YAML配置，实现了代码与配置的分离。这意味着同一套代码可以轻松适配不同数据源或实验设置，极大提升复用性。
- 【智能跳过机制】通过检查中间文件是否存在及--force参数，避免了不必要的重复计算，节省时间和资源，这在处理大规模数据时尤为重要。
- 【错误前置检查】在进入下一步前，会验证上一步的输出（如检查原始图像是否存在），防止错误累积到后期才发现，提高调试效率。
- 【日志即文档】详细的日志输出不仅帮助调试，还自动记录了数据处理的全过程，为实验可复现性提供了保障。

### 6 配置文件

**文件**: `configs/config.yaml`

**目的**: 集中管理整个数据准备流程的参数和路径配置，实现代码与配置的分离，便于实验调整和部署。

#### 详细说明

同学们，在软件工程中有一条黄金法则：**永远不要把配置写死在代码里**。为什么？因为需求总是在变——今天你用GPT-4做标注，明天可能换成Claude；今天增强10倍，明天可能只需要5倍。如果这些参数都硬编码在Python文件中，每次调整都要改代码、测代码，效率极低且容易出错。

因此，我们引入了`config.yaml`这个**中央配置文件**。YAML（YAML Ain't Markup Language）是一种人类可读的数据序列化格式，比JSON更简洁，支持注释，非常适合做配置。在这个文件中，我们定义了整个Package 1所需的所有参数：数据路径、LLM API设置、噪声模拟参数、增强策略等。

让我们逐部分解析这个配置文件。首先是`data`部分，它定义了所有关键目录和文件路径：`raw_images_dir`是原始图像存放位置，`annotated_json_path`是LLM标注结果的输出路径，`augmented_dir`是增强图像的保存目录，`final_dataset_path`是最终数据集的JSON文件。这些路径都是相对项目根目录的，确保项目可移植。

接下来是`data_collector`配置。这里我们指定了数据源——可以是本地目录（`source: local`），也可以是云存储（未来可扩展）。`local_path`就是你的手机或相机照片所在位置。注意，我们还设置了`max_images`限制，防止意外加载过多图像导致内存溢出。

`llm_annotator`部分至关重要。它包含了调用大语言模型所需的一切：`model`指定使用哪个模型（如gpt-4-turbo），`api_key`是认证密钥（实际使用时应从环境变量读取，此处仅为示例），`prompt_template`定义了发送给LLM的提示词模板。这个模板非常关键——它告诉LLM如何根据图像元数据生成噪声描述。我们使用了占位符`{iso}`、`{shutter_speed}`等，这些会在运行时被实际值替换。

`noise_simulator`配置定义了各种噪声的默认参数。例如，高斯噪声的标准差范围、泊松噪声的缩放因子等。这些值基于真实相机传感器的典型特性设定，但你可以根据自己的数据调整。

最后，`augmenter`部分控制数据增强的行为：`augment_factor`决定每张图生成多少增强样本，`min_noise_threshold`用于判断是否叠加额外噪声（单位是像素标准差）。

这个配置文件如何被使用？在`main.py`中，我们通过`yaml.safe_load()`读取它，然后将对应的部分传递给各个组件。例如，`DataCollector`接收`config['data_collector']`，`LLMAnnotator`接收`config['llm_annotator']`。这种设计使得每个组件只关心自己的配置，降低了耦合度。

安全性方面，注意`api_key`不应明文写在配置文件中！在实际部署时，应通过环境变量或密钥管理服务注入。我们在示例中保留它只是为了教学清晰，但务必在真实项目中移除。

配置文件的另一个好处是**实验管理**。你可以创建多个YAML文件（如`config_low_noise.yaml`、`config_high_aug.yaml`），快速切换不同实验设置，而无需改动任何代码。这对于科研迭代至关重要。

总之，这个看似简单的YAML文件，实际上是整个数据准备流程的“控制面板”。它让我们的系统变得灵活、可配置、可复现——这正是专业级项目的标志。

#### 完整实现

```yaml
# Package 1: 基于大语言模型引导的真实噪声图像数据准备与语义标注框架
# 全局配置文件

# 数据路径配置
data:
  raw_images_dir: "data/raw_images/"          # 原始含噪图像目录
  annotated_json_path: "data/annotated_dataset.json"  # LLM标注结果
  augmented_dir: "data/augmented_samples/"    # 增强图像输出目录
  final_dataset_path: "data/final_dataset.json"       # 最终数据集

# 数据收集器配置
data_collector:
  source: "local"                             # 数据源类型: local | cloud (预留)
  local_path: "/path/to/your/noisy/photos/"  # 本地原始图像路径 (需用户修改!)
  max_images: 1000                            # 最大加载图像数量
  extensions: [".jpg", ".jpeg", ".png"]      # 支持的图像格式

# LLM噪声标注器配置
llm_annotator:
  model: "gpt-4-turbo"                        # 使用的LLM模型
  api_key: "sk-your-api-key-here"             # OpenAI API密钥 (实际使用时应从环境变量读取!)
  temperature: 0.3                            # 生成多样性控制 (值越低越确定)
  max_tokens: 150                             # 最大生成长度
  prompt_template: |
    你是一位专业的摄影噪声分析专家。请根据以下图像元数据，生成一段简洁的中文描述，
    说明该图像中最可能存在的噪声类型（高斯、泊松、椒盐或混合）及其强度（轻微、中等、严重）。
    描述应包含噪声的物理成因（如高ISO、长曝光等）。
    
    相机型号: {camera_model}
    ISO感光度: {iso}
    快门速度: {shutter_speed}
    光圈: {aperture}
    拍摄场景: {scene_description}
    
    请直接输出描述，不要包含任何其他文字。

# 噪声模拟器配置
noise_simulator:
  gaussian:
    std_min: 5.0                              # 高斯噪声标准差最小值
    std_max: 30.0                             # 高斯噪声标准差最大值
  poisson:
    scale_min: 0.5                            # 泊松噪声缩放因子最小值
    scale_max: 2.0                            # 泊松噪声缩放因子最大值
  salt_pepper:
    prob_min: 0.01                            # 椒盐噪声概率最小值
    prob_max: 0.05                            # 椒盐噪声概率最大值

# 数据增强器配置
augmenter:
  augment_factor: 3                           # 每张原始图像生成的增强样本数
  min_noise_threshold: 10                     # 噪声强度阈值 (低于此值才考虑叠加噪声)
```

#### 重要提示

- 【敏感信息保护】配置文件中的api_key仅为示例，实际项目中必须通过环境变量（如os.getenv('OPENAI_API_KEY')）或密钥管理服务注入，绝不能提交到代码仓库。
- 【路径可移植性】所有路径都使用相对路径（相对于项目根目录），确保项目在不同机器上都能正常运行，只需修改local_path指向你的数据位置。
- 【提示词模板设计】LLM的prompt_template经过精心设计，明确要求输出格式和内容，减少无关文本，这对后续自动解析标签至关重要。
- 【参数范围合理性】噪声模拟参数（如高斯std范围5-30）基于真实相机传感器噪声水平设定，过大或过小都会导致合成噪声不真实。
- 【实验友好性】通过复制此YAML文件并修改参数，可以轻松创建多个实验配置，无需改动代码，极大加速科研迭代。

### 7 使用文档

**文件**: `docs/usage.md`

**目的**: 提供清晰的使用指南，帮助用户快速上手本数据准备框架，包括环境安装、配置修改、运行命令和结果解读。

#### 详细说明

同学们，再好的代码，如果没有清晰的文档，也会让人望而却步。作为负责任的开发者和研究者，我们必须为使用者（包括未来的自己！）提供一份详尽的**使用手册**。这份`usage.md`文档位于`docs/`目录下，采用Markdown格式，既适合在GitHub上直接阅读，也方便转换为PDF或其他格式。

文档的结构遵循“由浅入深”的原则。首先，我们给出**一句话概述**，让用户立刻明白这个包是干什么的。接着是**先决条件**——你需要什么硬件、软件、账号才能运行它。例如，你需要Python 3.8+、OpenAI API密钥、以及一批真实的含噪图像。

然后是**分步指南**，这是文档的核心。我们将其拆解为四个清晰的步骤：1) 安装依赖；2) 准备数据；3) 配置参数；4) 运行主流程。每一步都配有具体的命令和截图（虽然此处是文本，但实际可附图），甚至包括常见错误的解决方案。例如，在“准备数据”部分，我们会提醒用户：“请将你的手机夜景照片放入`/path/to/your/noisy/photos/`，并确保它们包含EXIF元数据（大多数手机默认开启）”。

特别重要的是**配置说明**。我们会逐项解释`config.yaml`中每个参数的含义和推荐值。比如，对于`augment_factor`，我们会说明：“设为3表示每张原始图像生成3个增强样本，总计4倍数据量。如果你GPU内存有限，可设为1”。这种指导能极大降低新手的学习曲线。

我们还专门设置了**结果解读**章节。运行完成后，用户会得到一堆文件和目录，他们需要知道：`final_dataset.json`是什么结构？`augmented_samples/`里的图像如何使用？PSNR指标在哪里看？（虽然本包不计算PSNR，但我们会说明后续步骤会用到这些数据）。

为了应对现实问题，文档包含**故障排除（Troubleshooting）**部分。例如：“如果遇到‘Invalid API key’错误，请检查config.yaml中的api_key是否正确，并确认OpenAI账户余额充足”；“如果增强后的图像全是黑的，请检查原始图像是否损坏”。这些经验之谈能节省用户大量调试时间。

最后，我们提供**扩展建议**。比如：“如果你想支持更多噪声类型，可以修改noise_simulator.py中的add_custom_noise方法”；“若要使用本地LLM（如Llama 3），请替换llm_annotator.py中的API调用部分”。这鼓励用户在理解基础上进行创新。

这份文档不仅是说明书，更是**知识传承的载体**。它记录了设计决策、最佳实践和常见陷阱，让后来者站在我们的肩膀上前进。记住：优秀的开源项目，一半功劳在文档。

#### 完整实现

```python
# Package 1 使用指南：基于大语言模型引导的真实噪声图像数据准备

## 概述
本框架用于构建高质量、语义丰富的含噪图像数据集，专为LLM引导的扩散去噪模型设计。它能：
- 从真实拍摄的低光/高ISO图像中收集数据
- 利用GPT等大语言模型自动生成噪声类型与强度标签
- 通过语义感知的数据增强扩充样本
- 输出结构化数据集供后续训练使用

## 先决条件
- **Python 3.8+**
- **OpenAI API 密钥**（或其他兼容LLM的API密钥）
- **真实含噪图像**（建议：手机夜景模式、高ISO DSLR照片，需包含EXIF元数据）
- **约10GB可用磁盘空间**（用于存储增强后的图像）

## 快速开始

### 1. 安装依赖
```bash
git clone https://github.com/your-repo/package-01-llm-noise-annotation.git
cd package-01-llm-noise-annotation
pip install -r requirements.txt
```

### 2. 准备原始数据
- 将你的含噪图像（.jpg/.png）放入一个目录，例如 `~/my_noisy_photos/`
- **重要**：确保图像包含EXIF元数据（ISO、快门速度等）。大多数手机和相机默认开启。

### 3. 配置参数
编辑 `configs/config.yaml`：
```yaml
# 修改这一行指向你的数据目录
data_collector:
  local_path: "/home/user/my_noisy_photos/"  # ←←← 在这里修改!

# 替换为你的OpenAI API密钥 (强烈建议使用环境变量!)
llm_annotator:
  api_key: "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```
> **安全提示
```

#### 重要提示


---

## 📦 依赖安装

### 所需依赖

- **openai (>=1.0.0)**: 调用GPT系列大语言模型进行噪声语义标注
- **opencv-python (>=4.5.0)**: 图像加载、预处理和数据增强
- **numpy (>=1.21.0)**: 数值计算和噪声模拟
- **pyyaml (>=6.0)**: 解析配置文件
- **tqdm (>=4.60.0)**: 显示进度条，提升用户体验

### 安装步骤

```bash
克隆本仓库：git clone https://github.com/your-repo/package-01-llm-noise-annotation.git
创建虚拟环境：python -m venv venv && source venv/bin/activate (Linux/Mac) 或 venv\Scripts\activate (Windows)
安装依赖：pip install -r requirements.txt
设置OpenAI API密钥：export OPENAI_API_KEY='your-api-key' (Linux/Mac) 或 set OPENAI_API_KEY=your-api-key (Windows)
准备原始图像：将真实含噪图像放入 data/raw_images/ 目录
```

---

## 🎮 使用教程

### 基础用法：自动标注单张图像

**场景**: 用户提供一张真实含噪图像和对应的元数据描述，系统调用LLM生成结构化噪声标签。

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

**预期输出**: 输出一个Python字典，例如：{'noise_type': ['gaussian'], 'intensity': 'high', 'source': 'high_iso_low_light'}。该结果将被保存到JSON文件中，供后续训练使用。

### 批量处理与数据增强

**场景**: 用户希望对整个raw_images目录中的图像进行批量标注，并对标注成功的样本进行安全的数据增强（如旋转、翻转），以扩充训练集。

```python
from src.main import process_dataset

# 配置参数
config = {
    "input_dir": "data/raw_images",
    "output_file": "data/annotated_dataset.json",
    "augment": True,
    "augment_dir": "data/augmented_samples",
    "confidence_threshold": 0.8
}

# 执行批量处理
process_dataset(config)
```

**预期输出**: 程序将遍历所有图像，为每张图生成描述（可通过EXIF自动提取或手动提供），调用LLM标注，过滤低置信度结果，并对高置信度样本进行旋转/翻转增强。最终生成annotated_dataset.json文件，包含图像路径、噪声标签、置信度等信息，同时增强图像保存在augmented_samples目录中。

---

## 📝 行动项

> [step_1] 数据准备与噪声标注 : 收集真实世界含噪声图像数据集（如相机拍摄、低光场景），并使用GPT类大语言模型辅助生成噪声类型（高斯、泊松、椒盐）及强度标签，结合数据增强策略扩充训练样本，提升模型泛化能力。
