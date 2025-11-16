@echo off
echo ========================================
echo   Aider 代码智能体服务启动脚本
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo [1/4] 检查依赖...
pip show aider-chat >nul 2>&1
if errorlevel 1 (
    echo [提示] 未安装 aider-chat，正在安装...
    pip install -r requirements_aider.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
) else (
    echo [✓] 依赖已安装
)

echo.
echo [2/4] 检查环境变量...
if not defined OPENAI_API_KEY (
    echo [警告] 未设置 OPENAI_API_KEY 环境变量
    echo [提示] 请在 .env 文件中配置或设置系统环境变量
    echo.
    set /p "API_KEY=请输入你的 OpenAI API Key (或按回车跳过): "
    if not "!API_KEY!"=="" (
        set OPENAI_API_KEY=!API_KEY!
        echo [✓] API Key 已设置
    )
) else (
    echo [✓] OPENAI_API_KEY 已配置
)

echo.
echo [3/4] 启动后端服务...
echo [提示] 服务将在 http://localhost:5000 运行
echo [提示] 按 Ctrl+C 停止服务
echo.

REM 启动 Flask 服务器
python api_server.py

pause

