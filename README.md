# InternAgent: When Agent Becomes the Scientist – Building Closed-Loop System from Hypothesis to Verification

[[ Paper 📓 ]](https://arxiv.org/abs/2505.16938) [[ Apply Page 💡 ]](https://discovery.intern-ai.org.cn) [[ Website 🏠 ]](https://alpha-innovator.github.io/InternAgent-project-page)

<i>
From One Idea to Autonomous Experimentation
</i>
</div>

## 🔥 News
  - <p style='text-align:justify'><i>2025.10.13</i>: &nbsp; Our InternAgent-1.0 code has been fully open-sourced, supporting end-to-end automation and autonomous evolution across 12 scientific research tasks.
  - <p style='text-align:justify'><i>2025.09.29</i>: &nbsp; 🔥 Our <b>deep research agent, FlowSearch</b>, demonstrates strong competitiveness across the GAIA, HLE, GPQA, and TRQA benchmarks, achieving state-of-the-art results on multiple tasks.
  - <p style='text-align:justify'><i>2025.09.12</i>: &nbsp; 🔥 Our latest <b>coding agent AutoMLGen</b> has achieved the championship in MLE-bench with <b>36.44%</b> medal rate, ranking <b>#1</b> among all competing methods, see details at <a href="https://github.com/openai/mle-bench">openai/mle-bench</a>. 
  - <p style='text-align:justify'><i>2025.08.06</i>: &nbsp; InternAgent now supports Intern-S1 which combines strong general-task capabilities with state-of-the-art performance on a wide range of scientific tasks. Check <a href="https://internlm.intern-ai.org.cn/api/document">here</a> for how to use Intern-S1.
  - <p style='text-align:justify'><i>2025.07.17</i>: &nbsp; The source code of InternAgent has been partially open-sourced. The complete version of InternAgent (covering 12 types of tasks for autonomous scientific research) will be open-sourced soon. This code repository can be used for full-cycle autonomous scientific research, ranging from hypothesis generation to automated experimental execution. It includes the source code for our initial version, covering paper retrieval, idea generation, coding, and experimental execution.
  - <p style='text-align:justify'><i>2025.07.10</i>: &nbsp; NovelSeek has be renamed to <b>InternAgent</b>. This change embodies our hopeful vision for autonomous scientific research framework, and we hope it will empower all researchers to achieve great scientific discoveries.</p>


## 📖 Overview

![InternAgent](/assets/internagent_overall.png)

InternAgent can support **12** types of scientific research tasks ranging from the AI field to the science field, including reaction yield prediction, molecular dynamics, power flow estimation, time series forecasting, transcription prediction, enhancer activity prediction, sentiment classification, 2D image classification, 3D point classification, 2D semantic segmentation, 3D autonomous driving, large vision-language model fine-tuning.

## 🌟 Core Features

![Framework](/assets/internagent_framework.png)

InternAgent covers three main capabilities: (1) **Self-evolving idea generation with human-interactive feedback**, (2) **Idea-to-methodology construction**, and (3) **Evolutionary experimental planning and execution**. 

It is a unified, closed-loop multi-agent system designed to automate and accelerate innovative research across scientific domains. Through intelligent agent collaboration, our system enables **end-to-end automation** from idea generation and methodology construction to experimental execution, dramatically enhancing research efficiency and creativity.

### 💡 Self-Evolving Idea Generation with Human-Interactive Feedback
- Autonomous generation, selection, and evolution of innovative research ideas through multi-agent collaboration
- Supports interactive human feedback, enabling continuous refinement of ideas with expert insights
- Dynamically integrates literature, code, and domain knowledge to inspire diverse innovation pathways

### 🏗️ Idea-to-Methodology Construction
- Systematically transforms creative ideas into actionable and verifiable research methodologies
- Integrates baseline code, literature, and expert knowledge to automatically generate comprehensive methodological frameworks
- Supports iterative refinement and traceability of research methods

### 🛠️ Evolutionary Experimental Planning and Execution
- Automates complex experimental workflow planning, code implementation, and debugging
- Employs exception-guided intelligent debugging to automatically identify and resolve code issues
- Enables adaptive evolution and continuous optimization of experimental plans

### 🤖 Multi-Agent Orchestration
- Coordinates specialized agents such as Survey, Coding, Idea Innovation, and Assessment Agents and so on 
- Manages data flow, task scheduling, and human interaction points for efficient and coherent research processes
- Supports extensibility and compatibility with diverse scientific tasks

---

**InternAgent** delivers an "end-to-end algorithmic innovation", empowering AI+X researchers to rapidly complete the full research loop—from idea to methodology to experimental validation—accelerating scientific discovery and breakthroughs.

## 🔬 Supported Research Tasks

- Suzuki Yield Prediction
- Molecular Dynamics Simulation
- Enhancer Activity Prediction
- Transcription Prediction for Perturbation Response
- Power Flow Estimation
- Time Series Forecasting
- Semantic Segmentation
- Image Classification
- Sentiment Analysis
- Point Cloud Classification
- Autonomous Driving
- VLM & LLM Fine-tuning
- ......

## 🎉 Benchmark Results

### Results on 12 different types of research tasks

The results report both maximum performance and mean performance (i.e., the average across runs with performance gains) achieved by InternAgent and Dolphin. InternAgent consistently improves upon the baseline and outperforms Dolphin across all tasks, spanning AI and scientific task domains.

#### Max Performance (per task)

| Task | Metric | Baseline | Dolphin | InternAgent |
|---|---|---:|---:|---:|
| AutoRYP | R^2 ↑ | 27.6 | 31.8 (+4.2) | **35.4 (+7.8)** |
| AutoMD | Forces-MAE ↓ | 0.158 | 0.152 | **0.148** |
| AutoPower | RMSE ↓ | 0.00473 | 0.00455 | **0.00426** |
| AutoTSF | MAE ↓ | 0.4382 | 0.4627 | **0.4331** |
| AutoTPPR | MSE ↓ | 0.197 | 0.173 | **0.146** |
| AutoEAP | HK-PCC ↑ | 0.65 | 0.76 | **0.79** |
| AutoSenCls | Acc ↑ | 91.0 | 92.5 (+1.5) | **93.5 (+2.5)** |
| Auto2DCls | Top-1 Acc ↑ | 81.2 | 82.0 (+0.8) | **83.3 (+2.1)** |
| Auto3DCls | OA ↑ | 91.0 | 93.9 (+2.9) | **95.5 (+4.5)** |
| Auto2DSeg | mIoU ↑ | 78.8 | - | **81.0 (+2.2)** |
| AutoPCDet | mAP ↑ | 65.0 | - | **65.9 (+0.9)** |
| AutoVLM | QA ↑ | 67.1 | - | **67.6 (+0.5)** |

#### Average Performance (per task)

| Task | Metric | Baseline | Dolphin | InternAgent |
|---|---|---:|---:|---:|
| AutoRYP | R^2 ↑ | 27.6 | 31.3 (+3.7) | **33.5 (+5.9)** |
| AutoMD | Forces-MAE ↓ | 0.158 | 0.155 | **0.152** |
| AutoPower | RMSE ↓ | 0.00473 | 0.00459 | **0.00447** |
| AutoTSF | MAE ↓ | 0.4382 | - | **0.4346** |
| AutoTPPR | MSE ↓ | 0.197 | 0.179 | **0.170** |
| AutoEAP | HK-PCC ↑ | 0.65 | 0.73 | **0.77** |
| AutoSenCls | Acc ↑ | 91.0 | 91.8 (+0.8) | **92.5 (+1.5)** |
| Auto2DCls | Top-1 Acc ↑ | 81.2 | 81.8 (+0.6) | **82.2 (+1.0)** |
| Auto3DCls | OA ↑ | 91.0 | 92.0 (+1.0) | **93.4 (+2.4)** |
| Auto2DSeg | mIoU ↑ | 78.8 | - | **80.1 (+1.3)** |
| AutoPCDet | mAP ↑ | 65.0 | - | **65.7 (+0.7)** |
| AutoVLM | QA ↑ | 67.1 | - | **67.6 (+0.5)** |


### 👨‍💻  MLE-Bench: Record-Breaking Performance in Just 12 Hours!

InternAgent-MLE (AutoMLGen) has achieved **36.44%** medal rate on the MLE-Bench, securing the **#1** position among all competing methods - and remarkably, this was accomplished in **only 12 hours** of running time!

| Agent | Low == Lite (%) | Medium (%) | High (%) | All (%) | Running Time (hours) | Date |
|---------|--------|-----------|---------|----------|--------|------
| [InternAgent-MLE](https://arxiv.org/abs/2510.08511) deepseek-r1 | 62.12 ± 3.03 | 26.32 ± 2.63 | 24.44 ± 2.22| **36.44 ± 1.18** | **12** | 2025-09-12	
| Neo multi-agent | 48.48 ± 1.52 | 29.82 ± 2.32	| 24.44 ± 2.22 | 34.22 ± 0.89 | 36 | 2025-07-28 
| R&D-Agent o3 + GPT-4.1 | 51.52 ± 6.9 | 19.3 ± 5.5 | 26.67 ± 0 | 30.22 ± 1.5 | 24 | 2025-08-15 
| ML-Master deepseek-r1 | 48.5 ± 1.5 | 20.2 ± 2.3 | 24.4 ± 2.2| 29.3 ± 0.8 | 12 | 2025-06-17 
| R&D-Agent o1-preview | 48.18 ± 2.49 | 8.95 ± 2.36 | 18.67 ± 2.98 | 22.4 ± 1.1 | 24 | 2025-05-14 
| AIDE o1-preview | 34.3 ± 2.4 | 8.8 ± 1.1 | 10.0 ± 1.9 | 16.9 ± 1.1 | 24 | 2024-10-08 
| AIDE gpt-4o-2024-08-06 | 19.0 ± 1.3 | 3.2 ± 0.5 | 5.6 ± 1.0 | 8.6 ± 0.5 | 24 | 2024-10-08 
| AIDE claude-3-5-sonnet-20240620 | 19.4 ± 4.9 | 2.6 ± 1.5 | 2.3 ± 2.3 | 7.5 ± 1.8 | 24 | 2024-10-08 
| OpenHands gpt-4o-2024-08-06 | 11.5 ± 3.4 | 2.2 ± 1.3 | 1.9 ± 1.9 | 5.1 ± 1.3 | 24 | 2024-10-08 
| AIDE llama-3.1-405b-instruct | 8.3 ± 2.6 | 1.2 ± 0.8 | 0.0 ± 0.0 | 3.1 ± 0.9 | 24 | 2024-10-08 
| MLAB gpt-4o-2024-08-06 | 4.2 ± 1.5 | 0.0 ± 0.0 | 0.0 ± 0.0 | 1.3 ± 0.5 |  24 | 2024-10-08 

### 🧪  GAIA, GPQA-diamond and HLE benchmarks  
We benchmark InternAgent-DR (FlowSearch) on a series of benchmarks, including GAIA, HLE and GPQA, and achieved SOTA results.

| Model/Framework | GAIA Avg | GPQA Avg | HLE text only | HLE All |
|-----------------|----------|----------|---------------|---------|
| Intern-S1 | 15.15 | 78.26 | 8.90 | 8.30 |
| Deepseek-R1 | 18.78 | 82.32 | 8.60 | - |
| o4-mini | 16.97 | 78.28 | 14.50 | 14.28 |
| GPT-5 | - | _85.35_ | 25.85 | 24.76 |
| OpenAI DR | 67.36 | - | - | 26.60 |
| Manus | 73.30 | - | - | - |
| Gemini Deep Research | - | - | - | 26.90 |
| MiroFlow | _74.50_ | - | 29.50 | 27.20 |
| OWL | 69.70 | - | - | - |
| X-Masters | - | - | **32.10** | _27.72_ |
| FlowSearch (Qwen-235B) | 58.79 | 66.16 | 15.04 | 14.84 |
| [FlowSearch (o4-mini)](https://arxiv.org/abs/2510.08521) | **76.96** | **87.37** | _31.60_ | **30.80** |


## 🚀 Quick Start

```bash
# 1) Create and activate env
conda create -n InternAgent python=3.11 -y
conda activate InternAgent

# 2) Install dependencies
pip install -r requirements.txt

# 3) Configure API keys
cp .env.example .env   # then edit .env to fill keys

# 4) Run planning + survey + engineering (text input)
python3 launch_planning.py \
  --text-input "如何利用深度学习算法，为图像去除噪声，在不损害图像原本质量的情况下?" \
  --max_rounds 2 \
  --max_papers 30 \
  --auto_survey \
  --non_interactive \
  --verbose \
  --enable_judger \
  --min_acceptable_score 8.0 \
  --enable_review \
  --max_revision_rounds 5 \
  --min_clarity_score 7.5 \
  --min_coherence_score 7.5 \
  --target_audience "intermediate developers"

# (Optional) Image input
python3 launch_planning.py \
  --image Image/your_image.png \
  --max_rounds 2 --max_papers 30 --auto_survey --non_interactive --verbose \
  --enable_judger --min_acceptable_score 8.0 --enable_review --max_revision_rounds 5 \
  --min_clarity_score 7.5 --min_coherence_score 7.5 --target_audience "intermediate developers"
```

### About the Research Tasks
We provide the `tasks` mentioned in our technical report as examples, and each task's code has a different training environment and dataset. Please refer to the code in each task's folder for configuration.


## Citation
```
@article{team2025novelseek,
  title={NovelSeek: When Agent Becomes the Scientist--Building Closed-Loop System from Hypothesis to Verification},
  author={Team, NovelSeek and Zhang, Bo and Feng, Shiyang and Yan, Xiangchao and Yuan, Jiakang and Yu, Zhiyin and He, Xiaohan and Huang, Songtao and Hou, Shaowei and Nie, Zheng and others},
  journal={arXiv preprint arXiv:2505.16938},
  year={2025}
}
```

```
@article{hu2025flowsearch,
  title={FlowSearch: Advancing deep research with dynamic structured knowledge flow},
  author={Yusong Hu, Runmin Ma, Yue Fan, Jinxin Shi, Zongsheng Cao, Yuhao Zhou, Jiakang Yuan, Xiangchao Yan, Wenlong Zhang, Lei Bai, Bo Zhang},
  journal={arXiv preprint arXiv:2510.08521},
  year={2025}
}
```

```
@article{du2025automlgen,
  title={AutoMLGen: Navigating Fine-Grained Optimization for Coding Agents},
  author={Shangheng Du, Xiangchao Yan, Dengyang Jiang, Jiakang Yuan, Yusong Hu, Xin Li, Liang He, Bo Zhang, Lei Bai},
  journal={arXiv preprint arXiv:2510.08521},
  year={2025}
}
```
