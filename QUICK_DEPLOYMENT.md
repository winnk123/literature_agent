# 文献智能体快速部署（5分钟版）

## ⚡ 快速开始

### 1️⃣ 安装依赖（2分钟）

```powershell
cd C:\Users\小新\Desktop\科创平台_cursor

# 安装主项目依赖
pip install -r requirements_aider.txt

# 安装文献智能体依赖
pip install -r literature_agent/literature_agent-123/requirements.txt
```

> **注意**: 如果遇到依赖冲突，已经修复：
> - ✅ 已移除 `contourpy==1.3.3`（需要 Python 3.11）
> - ✅ 已移除 `triton==3.4.0`（仅 Linux + CUDA）
> - ✅ 已移除 `torch==2.8.0`（仅 Linux + CUDA）
> - ✅ 已移除所有 `nvidia-*` CUDA 包

### 2️⃣ 确认配置（30秒）

API Keys 已在 `config/api.env` 配置：
```
✅ DEEPSEEK_API_KEY=sk-99b54ef5601f4b5983b79ac3c5135b7f
✅ S2_API_KEY=Ro1HBktXNV6XocSN5Cz7laVvPM7cROkk3iMKGzC8
✅ INS1_API_KEY=sk-ZqWBec4Wbq3jpQVV6e6nvizssBEipMPbyuY9tV1XQATzNZfH
```

### 3️⃣ 启动服务（10秒）

```powershell
python api_server.py
```

看到这个输出就成功了：
```
🚀 Aider Code Agent API 服务器启动中...
📡 监听端口: 5000
 * Running on http://127.0.0.1:5000
```

### 4️⃣ 测试（1分钟）

1. 打开前端页面
2. 进入任意项目
3. 点击 **"📄 文献"** 标签
4. 输入测试问题：
   ```
   深度学习在图像去噪领域的最新研究
   ```
5. 点击发送

**预期结果**: 返回结构化的文献综述报告 + 论文列表

---

## 🎯 API 使用说明

### 智能体分工

| 智能体 | 使用的 API | 功能 |
|--------|-----------|------|
| Task Decomposition, Generation, Reflection, Evolution, Method Development, Refinement, Engineer, Review, Literature Summary | `DEEPSEEK_API_KEY` | 所有 LLM 推理任务 |
| Survey Agent | `S2_API_KEY` | 文献检索（Semantic Scholar） |
| Judger Agent（可选） | `INS1_API_KEY` | 评分/评判 |

### 前端调用接口

文献模式自动通过以下接口触发：

**URL**: `POST /api/code/chat`

**请求体**:
```json
{
  "message": "你的研究问题",
  "language": "paper",
  "context": {
    "domain": "Computer Vision",
    "max_papers": 12
  }
}
```

**响应体**:
```json
{
  "success": true,
  "response": "文献综述报告（Markdown 格式）",
  "papers": [
    {
      "id": "0",
      "title": "论文标题",
      "authors": ["作者1", "作者2"],
      "year": 2024,
      "citationCount": 150,
      "score": 8.5
    }
  ],
  "metadata": {
    "search_queries": ["检索关键词"],
    "summary": {
      "problem_formulation": "问题阐述",
      "action_items": ["建议步骤"],
      "references": ["引用文献"]
    }
  }
}
```

---

## ❓ 故障排查

### 问题：依赖安装失败

**症状**: `ERROR: Could not find a version that satisfies the requirement XXX`

**解决**: 
```powershell
# 检查 Python 版本（需要 3.9 或 3.10）
python --version

# 如果是 3.8，升级：
conda create -n literature python=3.10
conda activate literature

# 重新安装
pip install -r literature_agent/literature_agent-123/requirements.txt
```

### 问题：后端启动报错

**症状**: `LiteratureAgentError: Missing required environment variables`

**解决**:
1. 确认 `config/api.env` 文件存在
2. 确认 API Keys 正确填写
3. 重启后端

### 问题：文献检索失败

**症状**: 返回 500 错误，控制台显示 S2 API 错误

**解决**:
1. 检查 `S2_API_KEY` 是否正确
2. 访问 https://api.semanticscholar.org/ 检查 API 状态
3. 确认 API 额度未超限

### 问题：DeepSeek 调用失败

**症状**: 返回 500 错误，控制台显示 DeepSeek API 错误

**解决**:
1. 登录 DeepSeek 控制台检查余额
2. 确认 `DEEPSEEK_API_KEY` 正确
3. 测试 API 连通性

---

## 📚 详细文档

完整部署指南请参考: [LITERATURE_AGENT_DEPLOYMENT.md](./LITERATURE_AGENT_DEPLOYMENT.md)

---

## ✅ 验证清单

部署成功后，确认以下项目：

- [ ] `pip install` 全部成功，无报错
- [ ] `python api_server.py` 启动成功
- [ ] 访问 `http://localhost:5000/api/health` 返回 `{"status": "ok"}`
- [ ] 前端"文献"标签可用
- [ ] 提交问题后返回文献综述报告
- [ ] 报告包含论文列表
- [ ] 控制台无 API 错误

全部打勾 = 部署成功！🎉

