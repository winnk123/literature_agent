# 🚀 快速开始指南

## 5 分钟快速体验

### 方式一: 仅前端体验（无需配置）

1. **打开平台**
   ```bash
   # 直接在浏览器中打开
   start index.html  # Windows
   open index.html   # Mac
   ```

2. **进入项目详情页**
   - 点击任意项目卡片

3. **使用代码智能体**
   - 在右侧 AI 面板点击"代码"标签
   - 输入: "用 Python 写一个快速排序函数"
   - 点击发送

4. **查看结果**
   - 查看 AI 生成的响应
   - 点击"文件"按钮查看代码

✅ **完成!** 你已经体验了代码智能体的基本功能（使用模拟响应）

---

### 方式二: 完整功能体验（需要配置）

#### 步骤 1: 安装依赖

```bash
pip install -r requirements_aider.txt
```

#### 步骤 2: 配置 API Key

**选项 A: 使用环境变量**
```bash
# Windows
set OPENAI_API_KEY=sk-your-api-key-here

# Linux/Mac
export OPENAI_API_KEY=sk-your-api-key-here
```

**选项 B: 使用 .env 文件**
```bash
# 复制示例文件
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# 编辑 .env 文件，填入你的 API Key
OPENAI_API_KEY=sk-your-api-key-here
```

#### 步骤 3: 启动后端服务

**使用启动脚本（推荐）:**
```bash
# Windows
start_aider_service.bat

# Linux/Mac
chmod +x start_aider_service.sh
./start_aider_service.sh
```

**或手动启动:**
```bash
python api_server.py
```

看到以下信息表示启动成功:
```
🚀 Aider Code Agent API 服务器启动中...
📡 监听端口: 5000
🔧 调试模式: 关闭
 * Running on http://0.0.0.0:5000
```

#### 步骤 4: 打开前端

在浏览器中打开 `index.html`

#### 步骤 5: 使用代码智能体

1. 进入任意项目详情页
2. 点击"代码"标签
3. 输入你的代码需求
4. 等待 AI 生成代码
5. 查看和下载生成的文件

✅ **完成!** 你现在可以使用完整的 Aider AI 功能了

---

## 常用命令

### 检查服务状态

```bash
# 测试后端 API
curl http://localhost:5000/api/health

# 预期响应:
# {"status":"ok","service":"Aider Code Agent","version":"1.0.0"}
```

### 停止服务

```bash
# 在运行服务的终端按 Ctrl+C
```

### 重启服务

```bash
# 停止服务后重新运行启动脚本
start_aider_service.bat  # Windows
./start_aider_service.sh  # Linux/Mac
```

---

## 使用示例

### 示例 1: 生成 Python 代码

**输入:**
```
写一个 Python 函数，实现二分查找算法
```

**AI 会生成:**
- 完整的函数实现
- 详细的注释
- 使用示例

### 示例 2: 生成 Web 应用

**输入:**
```
创建一个简单的 Flask Web 应用，包含首页和关于页面
```

**AI 会生成:**
- app.py (主应用文件)
- templates/index.html (首页)
- templates/about.html (关于页面)
- requirements.txt (依赖配置)

### 示例 3: 优化代码

**输入:**
```
优化这段代码的性能:
[粘贴你的代码]
```

**AI 会:**
- 分析代码性能瓶颈
- 提供优化建议
- 生成优化后的代码

---

## 故障排除

### 问题 1: 显示"模拟响应"

**原因:** 后端服务未启动

**解决:**
```bash
python api_server.py
```

---

### 问题 2: API Key 错误

**错误信息:** `OpenAI API key not found`

**解决:**
```bash
# 确保设置了环境变量
echo %OPENAI_API_KEY%  # Windows
echo $OPENAI_API_KEY   # Linux/Mac

# 如果为空，重新设置
set OPENAI_API_KEY=your-key  # Windows
export OPENAI_API_KEY=your-key  # Linux/Mac
```

---

### 问题 3: 端口被占用

**错误信息:** `Address already in use`

**解决方案 A: 修改端口**

编辑 `api_server.py`:
```python
port = 5001  # 改为其他端口
```

**解决方案 B: 停止占用端口的程序**
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <进程ID> /F

# Linux/Mac
lsof -i :5000
kill -9 <进程ID>
```

---

### 问题 4: 依赖安装失败

**解决:**
```bash
# 升级 pip
python -m pip install --upgrade pip

# 使用国内镜像
pip install -r requirements_aider.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 获取 API Key

### OpenAI API Key

1. 访问 https://platform.openai.com/
2. 注册/登录账号
3. 进入 API Keys 页面
4. 点击 "Create new secret key"
5. 复制生成的密钥

**注意:** 
- 新账号通常有免费额度
- API 调用会产生费用
- 妥善保管密钥，不要泄露

---

## 下一步

### 学习更多

- 📖 阅读 [使用指南](USAGE_GUIDE.md)
- 🔧 查看 [技术文档](AIDER_README.md)
- ✅ 运行 [测试](TEST_GUIDE.md)
- 📝 查看 [实现总结](IMPLEMENTATION_SUMMARY.md)

### 探索功能

- 尝试不同的编程语言
- 生成复杂的项目结构
- 使用代码编辑和优化功能
- 让 AI 解释复杂的算法

### 自定义配置

- 切换不同的 AI 模型
- 调整代码生成参数
- 自定义提示词模板

---

## 技术支持

遇到问题？

1. 查看 [故障排除](#故障排除) 部分
2. 阅读 [完整文档](AIDER_README.md)
3. 提交 Issue
4. 加入社区讨论

---

## 重要提示

⚠️ **安全提醒:**
- 不要在代码中包含敏感信息
- 定期检查 API 使用量
- 审查 AI 生成的代码
- 在生产环境使用前充分测试

💡 **最佳实践:**
- 提供清晰的需求描述
- 分步骤进行复杂任务
- 验证生成的代码
- 保持对话上下文

---

**祝你使用愉快！** 🎉

有任何问题或建议，欢迎反馈！

