#!/bin/bash

echo "========================================"
echo "  Aider 代码智能体服务启动脚本"
echo "========================================"
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 Python，请先安装 Python 3.8+"
    exit 1
fi

echo "[1/4] 检查依赖..."
if ! pip3 show aider-chat &> /dev/null; then
    echo "[提示] 未安装 aider-chat，正在安装..."
    pip3 install -r requirements_aider.txt
    if [ $? -ne 0 ]; then
        echo "[错误] 依赖安装失败"
        exit 1
    fi
else
    echo "[✓] 依赖已安装"
fi

echo ""
echo "[2/4] 检查环境变量..."
if [ -z "$OPENAI_API_KEY" ]; then
    echo "[警告] 未设置 OPENAI_API_KEY 环境变量"
    echo "[提示] 请在 .env 文件中配置或设置系统环境变量"
    echo ""
    read -p "请输入你的 OpenAI API Key (或按回车跳过): " API_KEY
    if [ ! -z "$API_KEY" ]; then
        export OPENAI_API_KEY=$API_KEY
        echo "[✓] API Key 已设置"
    fi
else
    echo "[✓] OPENAI_API_KEY 已配置"
fi

echo ""
echo "[3/4] 启动后端服务..."
echo "[提示] 服务将在 http://localhost:5000 运行"
echo "[提示] 按 Ctrl+C 停止服务"
echo ""

# 启动 Flask 服务器
python3 api_server.py

