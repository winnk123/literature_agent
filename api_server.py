"""
Flask API 服务器
提供代码智能体的 REST API 接口
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import io
import os
import sys
import traceback
from contextlib import redirect_stdout

import numpy as np
import requests

try:
    import torch
except Exception:
    torch = None
    print("警告: 未检测到 PyTorch，Notebook 执行环境中的 torch 代码可能不可用。")

from aider_service import process_code_request, AiderService

app = Flask(__name__)
CORS(app)

# 全局 CORS 响应头注入
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

# 配置
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max request size

# Notebook 执行会话
notebook_sessions = {}


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'ok',
        'service': 'Aider Code Agent',
        'version': '1.0.0'
    })


@app.route('/api/code/generate', methods=['POST'])
def generate_code():
    """
    生成代码接口
    
    请求体:
    {
        "prompt": "用户的代码需求描述",
        "language": "python",
        "context_files": []  // 可选
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'prompt' not in data:
            return jsonify({
                'success': False,
                'message': '缺少必要参数: prompt'
            }), 400
        
        request_data = {
            'action': 'generate',
            'prompt': data['prompt'],
            'language': data.get('language', 'python'),
            'files': data.get('context_files')
        }
        
        result = process_code_request(request_data)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


def deepseek_chat_completion(message: str, system_prompt: str = None, model: str = 'deepseek-chat') -> dict:
    """
    直接调用 DeepSeek 的 Chat Completions 接口（OpenAI 兼容）
    """
    api_key = os.environ.get('DEEPSEEK_API_KEY')
    if not api_key:
        return {'success': False, 'message': 'DEEPSEEK_API_KEY 未配置'}
    
    url = 'https://api.deepseek.com/chat/completions'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': system_prompt or 'You are a helpful coding assistant.'},
            {'role': 'user', 'content': message}
        ],
        'temperature': 0.7,
        'stream': False
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        if resp.status_code != 200:
            return {'success': False, 'message': f'DeepSeek 调用失败: HTTP {resp.status_code} - {resp.text}'}
        data = resp.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
        if not content:
            return {'success': False, 'message': 'DeepSeek 未返回内容'}
        return {'success': True, 'response': content}
    except requests.RequestException as e:
        return {'success': False, 'message': f'DeepSeek 请求异常: {str(e)}'}


def get_notebook_globals(session_id: str):
    """获取或初始化 notebook 会话的执行环境"""
    env = notebook_sessions.get(session_id)
    if env is None:
        env = {
            '__builtins__': __builtins__,
            'np': np,
            'torch': torch
        }
        notebook_sessions[session_id] = env
    return env


def run_python_cell(session_id: str, code: str) -> dict:
    """运行 Python 单元格代码"""
    env = get_notebook_globals(session_id)
    stdout = io.StringIO()
    try:
        with redirect_stdout(stdout):
            exec(compile(code, f'<notebook:{session_id}>', 'exec'), env, env)
        output = stdout.getvalue()
        return {
            'success': True,
            'output': output.strip()
        }
    except Exception as exc:
        return {
            'success': False,
            'output': stdout.getvalue().strip(),
            'message': str(exc),
            'traceback': traceback.format_exc()
        }


@app.route('/api/code/edit', methods=['POST'])
def edit_code():
    """
    编辑代码接口
    
    请求体:
    {
        "file_path": "要编辑的文件路径",
        "prompt": "编辑指令",
        "code": "当前代码内容"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'prompt' not in data:
            return jsonify({
                'success': False,
                'message': '缺少必要参数: prompt'
            }), 400
        
        request_data = {
            'action': 'edit',
            'prompt': data['prompt'],
            'file_path': data.get('file_path', 'temp.py'),
            'code': data.get('code')
        }
        
        result = process_code_request(request_data)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@app.route('/api/code/explain', methods=['POST'])
def explain_code():
    """
    解释代码接口
    
    请求体:
    {
        "code": "要解释的代码",
        "language": "python"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'code' not in data:
            return jsonify({
                'success': False,
                'message': '缺少必要参数: code'
            }), 400
        
        request_data = {
            'action': 'explain',
            'code': data['code'],
            'language': data.get('language', 'python')
        }
        
        result = process_code_request(request_data)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@app.route('/api/code/chat', methods=['POST'])
def code_chat():
    """
    代码对话接口（通用接口）
    
    请求体:
    {
        "message": "用户消息",
        "language": "python",
        "context": {
            "files": [],
            "conversation_history": []
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'message': '缺少必要参数: message'
            }), 400
        
        message = data['message']
        language = data.get('language', 'python')
        
        # 分析用户意图
        intent = analyze_intent(message)

        # 优先使用 DeepSeek 直接对话，保证快速响应；编辑/解释再走 Aider 流程
        if intent['action'] == 'generate':
            ds_result = deepseek_chat_completion(
                message,
                system_prompt='你是代码智能体，请用简洁、分步骤回答，并在需要时给出代码块。'
            )
            if ds_result.get('success'):
                return jsonify({
                    'success': True,
                    'response': ds_result['response'],
                    'files': []
                })
        
        request_data = {
            'action': intent['action'],
            'prompt': message,
            'language': language
        }
        
        # 如果是编辑或解释，需要额外的上下文
        if intent['action'] == 'edit' and 'context' in data:
            request_data['code'] = data['context'].get('current_code')
        elif intent['action'] == 'explain' and 'context' in data:
            request_data['code'] = data['context'].get('code_to_explain')
        
        result = process_code_request(request_data)
        
        # 添加对话式响应
        if result.get('success'):
            result['response'] = format_chat_response(result, intent['action'])
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@app.route('/api/notebook/run', methods=['GET', 'POST', 'OPTIONS'])
def notebook_run():
    """执行 Notebook 代码单元"""
    print(f"[DEBUG] notebook_run 被调用，方法: {request.method}")
    
    if request.method == 'OPTIONS':
        print("[DEBUG] 返回 OPTIONS 204")
        response = app.make_response(('', 204))
        return response
    
    if request.method == 'GET':
        return jsonify({'status': 'Notebook API is running'}), 200

    data = request.get_json() or {}
    code = data.get('code', '')
    language = data.get('language', 'python')
    session_id = data.get('sessionId') or 'default'

    if not code.strip():
        return jsonify({'success': False, 'message': '缺少必要参数: code'}), 400

    if language.lower() != 'python':
        return jsonify({'success': False, 'message': '当前仅支持 Python 单元格'}), 400

    result = run_python_cell(session_id, code)
    result['sessionId'] = session_id

    warnings = []
    if torch is None:
        warnings.append('未检测到 PyTorch，相关代码可能无法运行。请在后端环境安装 torch。')
    if warnings:
        result['warnings'] = warnings

    status_code = 200 if result.get('success') else 400
    return jsonify(result), status_code


@app.route('/api/notebook/session/reset', methods=['GET', 'POST', 'OPTIONS'])
def notebook_reset_session():
    """重置 Notebook 会话"""
    print(f"[DEBUG] notebook_reset_session 被调用，方法: {request.method}")
    
    if request.method == 'OPTIONS':
        print("[DEBUG] 返回 OPTIONS 204")
        response = app.make_response(('', 204))
        return response
    
    if request.method == 'GET':
        return jsonify({'status': 'Session reset API is running'}), 200

    data = request.get_json() or {}
    session_id = data.get('sessionId')
    if not session_id:
        return jsonify({'success': False, 'message': '缺少必要参数: sessionId'}), 400

    notebook_sessions.pop(session_id, None)
    return jsonify({'success': True, 'sessionId': session_id})


def analyze_intent(message: str) -> dict:
    """
    分析用户意图
    
    Args:
        message: 用户消息
        
    Returns:
        包含意图信息的字典
    """
    message_lower = message.lower()
    
    # 编辑意图关键词
    edit_keywords = ['修改', '改', '优化', '重构', '修复', 'bug', '错误', '更新']
    # 解释意图关键词
    explain_keywords = ['解释', '说明', '什么意思', '怎么工作', '原理', '为什么']
    
    if any(keyword in message_lower for keyword in edit_keywords):
        return {'action': 'edit', 'confidence': 0.8}
    elif any(keyword in message_lower for keyword in explain_keywords):
        return {'action': 'explain', 'confidence': 0.8}
    else:
        return {'action': 'generate', 'confidence': 0.9}


def format_chat_response(result: dict, action: str) -> str:
    """
    格式化对话响应
    
    Args:
        result: 处理结果
        action: 操作类型
        
    Returns:
        格式化的响应文本
    """
    if action == 'generate':
        file_count = len(result.get('files', []))
        if file_count > 0:
            file_list = '\n'.join([f"• {f['name']}" for f in result['files']])
            return f'我已经为你生成了 {file_count} 个文件：\n\n{file_list}\n\n你可以点击右上角的"文件"按钮查看和下载这些文件。'
        else:
            return "代码已生成完成。"
    
    elif action == 'edit':
        return "我已经根据你的要求修改了代码。请查看更新后的文件。"
    
    elif action == 'explain':
        return result.get('explanation', '代码解释已生成。')
    
    return result.get('message', '操作完成。')


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': '接口不存在'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': '服务器内部错误'
    }), 500


if __name__ == '__main__':
    # 检查环境变量
    if not os.environ.get('OPENAI_API_KEY'):
        print("警告: 未设置 OPENAI_API_KEY 环境变量")
        print("请设置环境变量或在 aider_service.py 中配置 API 密钥")
    
    # 启动服务器
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"🚀 Aider Code Agent API 服务器启动中...")
    print(f"📡 监听端口: {port}")
    print(f"🔧 调试模式: {'开启' if debug else '关闭'}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)

