# 文献智能体完整部署指南

## 📋 前置准备

### 1. 系统要求
- Windows 10/11
- Python 3.9 或 3.10（已安装且在 PATH 中）
- Git（可选，用于更新代码）

### 2. 获取 API Keys

#### DeepSeek API Key
1. 访问 https://platform.deepseek.com
2. 注册账号并充值
3. 在控制台获取 API Key

#### Semantic Scholar API Key
1. 访问 https://www.semanticscholar.org/product/api
2. 注册账号
3. 申请 API Key（免费版有限额）

---

## 🚀 完整部署步骤

### 步骤 1: 克隆/下载 literature_agent 仓库

**方式 A: 使用 Git（推荐）**
```powershell
cd C:\Users\小新\Desktop\科创平台_cursor
git clone https://github.com/winnk123/literature_agent.git
```

**方式 B: 手动下载**
1. 访问 https://github.com/winnk123/literature_agent
2. 点击 "Code" -> "Download ZIP"
3. 解压到 `C:\Users\小新\Desktop\科创平台_cursor\literature_agent\`
4. 确保解压后的目录结构为 `literature_agent/literature_agent-123/`

### 步骤 2: 验证目录结构

确保以下目录存在：
```
科创平台_cursor/
├── api_server.py
├── literature_agent_service.py
├── config/
│   └── api.env          # API 配置文件
└── literature_agent/
    └── literature_agent-123/
        ├── config/
        │   └── default_config.yaml
        ├── internagent/
        └── requirements.txt
```

### 步骤 3: 配置 API Keys

API Keys 已经配置在 `config/api.env`：
```env
DEEPSEEK_API_KEY=sk-99b54ef5601f4b5983b79ac3c5135b7f
S2_API_KEY=Ro1HBktXNV6XocSN5Cz7laVvPM7cROkk3iMKGzC8
INS1_API_KEY=sk-ZqWBec4Wbq3jpQVV6e6nvizssBEipMPbyuY9tV1XQATzNZfH
INS1_API_BASE_URL=https://chat.intern-ai.org.cn/api/v1/
```

### 步骤 4: 安装 Python 依赖

**4.1 安装主项目依赖**
```powershell
cd C:\Users\小新\Desktop\科创平台_cursor
pip install -r requirements_aider.txt
```

**4.2 安装文献智能体依赖**
```powershell
pip install -r literature_agent/literature_agent-123/requirements.txt
```

> **注意**: 如果遇到版本冲突，请确保使用 Python 3.9 或 3.10

### 步骤 5: 修改 api_server.py 加载环境变量

在 `api_server.py` 文件最顶部（在所有 import 之前）添加：

```python
from dotenv import load_dotenv
load_dotenv("config/api.env")
```

完整示例：
```python
"""
Flask API 服务器
提供代码智能体的 REST API 接口
"""

from dotenv import load_dotenv
load_dotenv("config/api.env")  # 👈 添加这两行

from flask import Flask, request, jsonify
from flask_cors import CORS
# ... 其他 imports
```

### 步骤 6: 启动后端服务

```powershell
cd C:\Users\小新\Desktop\科创平台_cursor
python api_server.py
```

**预期输出:**
```
🚀 Aider Code Agent API 服务器启动中...
📡 监听端口: 5000
🔧 调试模式: 关闭
 * Running on http://127.0.0.1:5000
```

### 步骤 7: 测试文献智能体

**7.1 打开前端页面**
```
http://localhost:5000 或你的前端地址
```

**7.2 测试文献模式**
1. 进入任意项目详情页
2. 点击 "📄 文献" 标签
3. 输入测试问题，例如：
   ```
   深度学习在图像去噪领域的最新研究进展
   ```
4. 点击发送

**预期结果:**
- 显示 "正在检索相关文献..." 思考动画
- 返回结构化的文献综述报告
- 包含引用的论文列表
- 显示打字机效果

---

## 📊 API 分配方案

| API Key | 用途 | 使用的智能体 |
|---------|------|------------|
| `DEEPSEEK_API_KEY` | 主力 LLM | Task Decomposition, Generation, Reflection, Evolution, Method Development, Refinement, Engineer, Review, Literature Summary |
| `S2_API_KEY` | 文献检索 | Survey Agent (Semantic Scholar API) |
| `INS1_API_KEY` | 备选模型 | Judger Agent (可选) |

---

## 🔧 配置说明

### 修改模型配置

如果需要调整哪个智能体使用哪个模型，编辑：
```
literature_agent/literature_agent-123/config/default_config.yaml
```

示例：让 Judger Agent 使用 Intern S1
```yaml
agents:
  judger:
    model_provider: "interns1"  # 从 openai 改为 interns1
```

### 调整文献检索参数

在 `literature_agent_service.py` 中调整：
```python
def run(
    self,
    question: str,
    domain: Optional[str] = None,
    background: str = "",
    max_papers: int = 12,  # 👈 修改这里调整检索论文数量
    guidance: Optional[List[str]] = None,
) -> Dict[str, Any]:
```

---

## 🐛 常见问题

### 问题 1: ModuleNotFoundError: No module named 'internagent'

**原因**: literature_agent 目录结构不对

**解决**:
```powershell
# 检查目录是否存在
dir literature_agent\literature_agent-123\internagent

# 如果不存在，重新下载仓库
```

### 问题 2: LiteratureAgentError: Missing required environment variables

**原因**: API Keys 未正确加载

**解决**:
1. 确认 `config/api.env` 文件存在
2. 确认 `api_server.py` 顶部有 `load_dotenv("config/api.env")`
3. 重启后端服务

### 问题 3: 文献检索失败 (S2 API 错误)

**原因**: Semantic Scholar API Key 无效或超额

**解决**:
1. 检查 API Key 是否正确
2. 查看 API 使用额度：https://www.semanticscholar.org/product/api
3. 如果超额，等待重置或升级到付费版

### 问题 4: DeepSeek API 调用失败

**原因**: API Key 无效或余额不足

**解决**:
1. 登录 DeepSeek 控制台检查余额
2. 确认 API Key 正确
3. 检查网络连接

### 问题 5: 安装依赖时出现 Python 版本错误

**原因**: 使用了 Python 3.8 或更低版本

**解决**:
```powershell
# 检查 Python 版本
python --version

# 如果低于 3.9，升级 Python 或使用虚拟环境
conda create -n literature python=3.10
conda activate literature
```

---

## 📝 前端调用示例

文献模式会自动通过 `/api/code/chat` 接口调用，请求格式：

```javascript
fetch('http://localhost:5000/api/code/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message: "深度学习在图像去噪领域的最新研究进展",
    language: "paper",  // 👈 关键：触发文献模式
    context: {
      domain: "Computer Vision",
      max_papers: 15,
      manual_guidance: ["关注2023-2024年的最新论文"]
    }
  })
})
```

**响应格式:**
```json
{
  "success": true,
  "response": "# 文献综述报告\n\n## 1. 问题阐述\n...",
  "papers": [
    {
      "id": "0",
      "title": "Deep Learning for Image Denoising: A Survey",
      "authors": ["Zhang et al."],
      "year": 2024,
      "citationCount": 150,
      "score": 8.5
    }
  ],
  "metadata": {
    "search_queries": ["KeywordQuery(\"deep learning image denoising\")"],
    "summary": {
      "problem_formulation": "...",
      "action_items": ["..."],
      "references": [...]
    }
  }
}
```

---

## 🎯 验证部署成功

运行以下检查清单：

- [ ] `python api_server.py` 成功启动，无报错
- [ ] 访问 `http://localhost:5000/api/health` 返回 `{"status": "ok"}`
- [ ] 前端"文献"标签可正常输入
- [ ] 提交问题后显示"思考中"动画
- [ ] 收到结构化的文献综述报告
- [ ] 报告包含引用的论文列表
- [ ] 控制台无 API Key 相关错误

---

## 📚 相关文档

- [DeepSeek API 文档](https://platform.deepseek.com/docs)
- [Semantic Scholar API 文档](https://api.semanticscholar.org/)
- [InternAgent GitHub](https://github.com/winnk123/literature_agent)
- [原项目 DEEPSEEK_SETUP_GUIDE.md](./DEEPSEEK_SETUP_GUIDE.md)

---

## 🆘 获取帮助

如遇到问题：
1. 检查后端控制台日志
2. 查看浏览器开发者工具 Network 标签
3. 参考上述"常见问题"章节
4. 确认所有 API Keys 有效且有余额

