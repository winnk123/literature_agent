# DeepSeek API 配置指南

## 🎯 目标

将 AI Agent 智能体切换为使用 DeepSeek API，实现：
- ✅ 文献助手使用 DeepSeek
- ✅ 科研助手使用 DeepSeek  
- ✅ 代码助手使用 DeepSeek
- ✅ 打字机效果显示回复
- ✅ 会话历史持久化
- ✅ 文件累积保存

---

## 📋 前置准备

### 1. 获取 DeepSeek API Key

1. 访问 DeepSeek 官网或代理平台
2. 注册账号并充值（确保有余额）
3. 获取 API Key

### 2. 确认环境

- Anaconda 环境已激活（如 `AI_course`）
- Python 3.8+
- 已安装 aider-chat

---

## 🔧 配置步骤（Anaconda 环境）

### 步骤 1: 激活 Conda 环境

```cmd
conda activate AI_course
cd C:\Users\小新\Desktop\科创平台_cursor
```

### 步骤 2: 安装/升级依赖

```cmd
pip install --upgrade aider-chat
pip install flask flask-cors python-dotenv
```

### 步骤 3: 设置环境变量（临时）

```cmd
set DEEPSEEK_API_KEY=你的DeepSeek密钥
set API_PROVIDER=deepseek
set AIDER_MODEL=deepseek
```

### 步骤 4: 验证 Aider 能否使用 DeepSeek

```cmd
aider --model deepseek --api-key deepseek=%DEEPSEEK_API_KEY% --message "写一个Python快速排序函数"
```

**预期结果**: 
- 能够成功生成代码文件
- 没有 "Insufficient Balance" 错误
- 没有 "LLM Provider NOT provided" 错误

### 步骤 5: 修改后端代码

需要修改 `aider_service.py` 中的三处调用 aider 的地方，添加 `--api-key` 参数。

**在 `generate_code` 方法中（第 44-60 行）**:

```python
cmd = [
    'aider',
    '--yes',
    '--no-git',
    f'--model={self.model}',
]

# 添加 API key 参数
if self.api_key:
    cmd.extend(['--api-key', f'deepseek={self.api_key}'])

cmd.extend(['--message', prompt])

# 如果有上下文文件，添加到命令中
if context_files:
    cmd.extend(context_files)

# 环境变量
env = os.environ.copy()
```

**同样修改 `edit_code` 和 `explain_code` 方法**。

### 步骤 6: 修改 `aider_service.py` 构造函数

```python
def __init__(self, api_key: Optional[str] = None, model: str = "deepseek"):
    """
    初始化 Aider 服务
    
    Args:
        api_key: DeepSeek API密钥（如果不提供，将从环境变量读取）
        model: 使用的模型，默认为 deepseek
    """
    self.api_key = api_key or os.environ.get('DEEPSEEK_API_KEY')
    self.model = model
    self.work_dir = Path(tempfile.mkdtemp(prefix='aider_'))
```

### 步骤 7: 启动后端服务

```cmd
python api_server.py
```

或使用启动脚本：

```cmd
start_aider_service.bat
```

**确认输出**:
```
🚀 Aider Code Agent API 服务器启动中...
📡 监听端口: 5000
 * Running on http://127.0.0.1:5000
```

### 步骤 8: 测试前端

1. 刷新浏览器页面（Ctrl + F5）
2. 进入任意项目详情页
3. 选择任意 Agent 类型（文献/科研/代码）
4. 输入问题并发送
5. 观察：
   - ✅ 显示思考中动画
   - ✅ AI 回复逐字显示（打字机效果）
   - ✅ 代码直接在对话中展示
   - ✅ 文件按钮可点击

---

## 📚 文献智能体（DeepSeek）部署流程

1. **拉取模型仓库**  
   ```powershell
   cd C:\Users\小新\Desktop\科创平台_cursor
   git clone https://github.com/winnk123/literature_agent.git
   # 如果 Git 访问受限，可手动下载 zip，解压到 literature_agent/
   ```

2. **安装依赖**  
   ```powershell
   pip install -r requirements_aider.txt
   pip install -r literature_agent/literature_agent-123/requirements.txt
   ```

3. **设置环境变量（PowerShell 永久方式）**  
   ```powershell
   setx DEEPSEEK_API_KEY "sk-xxxxxx"
   setx S2_API_KEY "semanticscholar_xxxxxx"
   ```
   > **说明**  
   > - `DEEPSEEK_API_KEY`：调用 DeepSeek Chat Completions，已在 `OpenAIModel` 默认读取。  
   > - `S2_API_KEY`：用于 `PaperSurvey` 调用 Semantic Scholar Graph API。  
   > - 如需自定义 API 入口，可额外设置 `OPENAI_API_BASE_URL=https://api.deepseek.com/v1`。

4. **启动后端**  
   ```powershell
   cd C:\Users\小新\Desktop\科创平台_cursor
   python api_server.py
   ```
   文献模式请求（`language=paper`）会自动进入 `literature_agent_service`，拉起 `SurveyAgent + LiteratureSummaryAgent` 生成完整报告，并返回：
   - `response`：结构化总结（供前端气泡显示）  
   - `papers`：高分文献清单  
   - `metadata.summary`：包含 `problem_formulation / action_items / references` 等字段  
   - `metadata.search_queries / round_results`：所有检索指令及轮次状态

5. **前端使用**  
   - 进入“文献”标签输入问题即可，无需额外按钮。  
   - 若要限制开销，可在前端 `context` 中传 `max_papers`，或在 `literature_agent_service.run()` 里修改默认值。

---

## 🎨 新功能展示

### 1. 打字机效果

AI 回复时，文字会像 ChatGPT 一样逐字显示：

```
AI: 我█
AI: 我已█
AI: 我已经█
AI: 我已经为█
AI: 我已经为你█
AI: 我已经为你生█
...
```

**速度**: 每个字符 20ms（可在代码中调整 `typingSpeed`）

### 2. DeepSeek 真实回复

所有三种模式都会调用 DeepSeek API：

- **文献模式**: `作为文献助手，请为以下主题推荐相关文献：...`
- **科研模式**: `作为科研助手，请为以下研究问题提供建议：...`
- **代码模式**: 直接发送用户的代码需求

### 3. 对话中展示代码

生成代码后，直接在对话气泡中显示：

```
┌─────────────────────────────────┐
│ AI (打字机效果显示中...)         │
│ ┌───────────────────────────┐   │
│ │ 我已经为你生成了代码...    │   │
│ │                           │   │
│ │ ┌─────────────────────┐   │   │
│ │ │ 📄 quicksort.py     │   │   │
│ │ │ def quicksort(arr): │   │   │
│ │ │   ...               │   │   │
│ │ └─────────────────────┘   │   │
│ └───────────────────────────┘   │
└─────────────────────────────────┘
```

---

## 🐛 常见问题

### 问题 1: "Insufficient Balance"

**原因**: DeepSeek 账号余额不足

**解决**: 
1. 登录 DeepSeek 控制台
2. 充值或申请测试额度
3. 确认余额充足后重试

### 问题 2: "LLM Provider NOT provided"

**原因**: aider 不认识 `deepseek` 这个模型名

**解决**: 
1. 升级 aider: `pip install --upgrade aider-chat`
2. 或使用 OpenRouter 等代理: `--model openrouter/deepseek/...`

### 问题 3: 打字机效果太快/太慢

**调整速度**: 在 `app.js` 中修改 `typingSpeed` 变量

```javascript
const typingSpeed = 20;  // 改为 10（更快）或 50（更慢）
```

### 问题 4: 文献/科研模式没有调用 DeepSeek

**检查**: 
1. 后端服务是否正常运行
2. 浏览器控制台是否有网络错误
3. 如果 API 调用失败，会自动降级到模拟响应

---

## 📊 功能验证

### 测试清单

- [ ] 后端服务启动成功
- [ ] 命令行 aider 能调用 DeepSeek
- [ ] 前端发送消息后显示思考动画
- [ ] AI 回复有打字机效果
- [ ] 代码在对话中直接显示
- [ ] 文件按钮可点击，显示所有文件
- [ ] 切换项目后返回，会话保持
- [ ] 生成多个文件，文件列表累积显示

### 调试信息

在浏览器控制台（F12）查看：

```
API 返回结果: {success: true, response: "...", files: [...]}
使用模拟文件，按钮已启用
会话已保存: ai 消息，模式: code
文件列表已保存到 localStorage
```

---

## 💡 优化建议

### 1. 调整打字速度

根据内容长度动态调整：

```javascript
// 短消息慢一点，长消息快一点
const typingSpeed = content.length > 500 ? 10 : 20;
```

### 2. 跳过打字效果

如果用户觉得打字太慢，可以添加"跳过"按钮：

```javascript
// 点击消息可以立即显示完整内容
contentEl.addEventListener('click', () => {
  contentEl.textContent = content;
  currentIndex = content.length;
});
```

### 3. 代码高亮

如果想要语法高亮，可以集成 highlight.js：

```html
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
```

---

## 🎯 下一步

1. **刷新页面** (Ctrl + F5)
2. **测试打字机效果** - 发送任意消息
3. **测试 DeepSeek 调用** - 确保后端服务运行
4. **测试会话持久化** - 切换项目后返回
5. **测试文件累积** - 连续生成多个文件

---

**现在所有功能都已实现！** 🎉

- ✅ 打字机效果
- ✅ DeepSeek API 调用
- ✅ 会话持久化
- ✅ 文件累积保存
- ✅ 代码同步展示

