# Aider 代码智能体集成文档

## 概述

本项目集成了 [Aider AI](https://github.com/Aider-AI/aider) 作为代码智能体，提供强大的代码生成、编辑和解释功能。

## 功能特性

### 1. 代码生成
- 根据自然语言描述生成完整的代码
- 支持多种编程语言（Python, JavaScript, Java, C, C++, Go, Rust 等）
- 自动生成相关配置文件和依赖文件

### 2. 代码编辑
- 智能修改现有代码
- 优化和重构代码
- 修复代码中的 bug

### 3. 代码解释
- 详细解释代码功能和逻辑
- 分析代码的关键部分
- 提供最佳实践建议

## 安装步骤

### 1. 安装 Python 依赖

```bash
pip install -r requirements_aider.txt
```

### 2. 安装 Aider

```bash
pip install aider-chat
```

### 3. 配置 API 密钥

创建 `.env` 文件并添加以下内容：

```env
OPENAI_API_KEY=your_openai_api_key_here
```

或者在系统环境变量中设置：

**Windows:**
```cmd
set OPENAI_API_KEY=your_openai_api_key_here
```

**Linux/Mac:**
```bash
export OPENAI_API_KEY=your_openai_api_key_here
```

## 使用方法

### 启动后端服务

```bash
python api_server.py
```

服务器将在 `http://localhost:5000` 启动。

### API 接口

#### 1. 生成代码

**端点:** `POST /api/code/generate`

**请求体:**
```json
{
  "prompt": "创建一个Python函数，用于计算斐波那契数列",
  "language": "python",
  "context_files": []
}
```

**响应:**
```json
{
  "success": true,
  "message": "代码生成成功",
  "files": [
    {
      "name": "fibonacci.py",
      "path": "fibonacci.py",
      "content": "def fibonacci(n):\n    ...",
      "size": "1.2 KB",
      "type": "Python"
    }
  ]
}
```

#### 2. 编辑代码

**端点:** `POST /api/code/edit`

**请求体:**
```json
{
  "file_path": "fibonacci.py",
  "prompt": "添加错误处理，确保输入是正整数",
  "code": "def fibonacci(n):\n    ..."
}
```

#### 3. 解释代码

**端点:** `POST /api/code/explain`

**请求体:**
```json
{
  "code": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
  "language": "python"
}
```

#### 4. 代码对话（通用接口）

**端点:** `POST /api/code/chat`

**请求体:**
```json
{
  "message": "帮我写一个快速排序算法",
  "language": "python",
  "context": {
    "files": [],
    "conversation_history": []
  }
}
```

## 前端集成

前端已经集成了代码智能体功能：

1. 在 AI 智能体对话框中选择"代码"标签
2. 输入你的代码需求
3. AI 将自动生成代码并显示在文件列表中
4. 点击"文件"按钮查看和下载生成的代码

### 前端调用示例

```javascript
// 发送代码生成请求
async function generateCode(prompt, language) {
  const response = await fetch('http://localhost:5000/api/code/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: prompt,
      language: language
    })
  });
  
  const result = await response.json();
  return result;
}
```

## 配置选项

### 模型选择

在 `aider_service.py` 中可以配置使用的模型：

```python
service = AiderService(model="gpt-4")  # 或 "gpt-3.5-turbo", "claude-3-opus" 等
```

### 支持的模型

- OpenAI: `gpt-4`, `gpt-4-turbo`, `gpt-3.5-turbo`
- Anthropic: `claude-3-opus`, `claude-3-sonnet`, `claude-3-haiku`
- 其他: 查看 [Aider 文档](https://aider.chat/docs/llms.html)

## 高级功能

### 1. 多文件上下文

```python
request_data = {
    'action': 'generate',
    'prompt': '创建一个Web应用',
    'language': 'python',
    'files': ['app.py', 'models.py', 'views.py']
}
```

### 2. 代码重构

```python
request_data = {
    'action': 'edit',
    'prompt': '将这个函数重构为类方法',
    'file_path': 'utils.py'
}
```

### 3. 代码审查

```python
request_data = {
    'action': 'explain',
    'prompt': '审查这段代码并提供改进建议',
    'code': your_code_here
}
```

## 故障排除

### 问题 1: API 密钥错误

**错误信息:** `OpenAI API key not found`

**解决方案:**
- 确保已设置 `OPENAI_API_KEY` 环境变量
- 检查 API 密钥是否有效
- 确认 API 密钥有足够的配额

### 问题 2: Aider 未安装

**错误信息:** `aider: command not found`

**解决方案:**
```bash
pip install aider-chat
```

### 问题 3: 端口被占用

**错误信息:** `Address already in use`

**解决方案:**
- 修改 `api_server.py` 中的端口号
- 或者停止占用该端口的其他服务

## 性能优化

### 1. 使用缓存

对于重复的请求，可以实现缓存机制：

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_generate_code(prompt, language):
    # 生成代码逻辑
    pass
```

### 2. 异步处理

对于耗时的代码生成任务，可以使用异步处理：

```python
from celery import Celery

app = Celery('aider_tasks')

@app.task
def async_generate_code(prompt, language):
    # 异步生成代码
    pass
```

## 安全注意事项

1. **API 密钥保护**: 不要将 API 密钥提交到版本控制系统
2. **输入验证**: 对用户输入进行严格验证
3. **速率限制**: 实施 API 调用速率限制
4. **代码沙箱**: 生成的代码在沙箱环境中执行

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目基于 Apache-2.0 许可证开源。

## 相关链接

- [Aider AI 官方网站](https://aider.chat/)
- [Aider AI GitHub](https://github.com/Aider-AI/aider)
- [Aider AI 文档](https://aider.chat/docs/)

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件
- 加入讨论组

---

**注意**: 使用 Aider AI 需要有效的 OpenAI API 密钥或其他支持的 LLM API 密钥。

