"""
基于 LangGraph 的办公智能体 Web 界面
FastAPI + 前端界面
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import os
import uuid
import asyncio
from typing import Optional, Dict, List
from datetime import datetime
from dotenv import load_dotenv
from pydantic import BaseModel

# 加载环境变量
load_dotenv()

# 导入项目模块
from graph.document_graph import process_document
from graph.compliance_graph import run_compliance_flow
from graph.daily_tech_graph import run_daily_tech_flow
from tools.file_tools import (
    detect_file_type,
    get_file_info,
    list_supported_formats,
    read_file
)
from tools.document_tools import create_summary_card, markdown_to_docx
from agents.multi_agents import multi_agent_system
from agents.prompt_manager import prompt_manager
from langchain_core.messages import HumanMessage

# 创建 FastAPI 应用
app = FastAPI(
    title="AgentDesk - 资管智能体工作台",
    description="专为资管行业打造的多智能体协作平台",
    version="1.0.0"
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 配置模板目录
templates = Jinja2Templates(directory="templates")

# 配置文件上传目录
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """返回主页"""
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>办公智能体助手</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            :root {
                --bg-primary: #0A0A0A;
                --bg-secondary: #121212;
                --primary: #FF6B00;
                --primary-gradient: linear-gradient(135deg, #FF8800 0%, #FF6B00 100%);
                --text-primary: #FFFFFF;
                --text-secondary: #A1A1AA;
                --glass-bg: rgba(255, 255, 255, 0.03);
                --glass-border: 1px solid rgba(255, 255, 255, 0.08);
                --glass-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.36);
                --backdrop-blur: blur(16px);
                --radius-lg: 24px;
                --radius-md: 16px;
            }

            body {
                background-color: var(--bg-primary);
                color: var(--text-primary);
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                padding: 0;
                min-height: 100vh;
            }

            .background {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: radial-gradient(circle at 50% 50%, rgba(255, 107, 0, 0.05) 0%, transparent 50%);
                z-index: -1;
            }

            .hero {
                background: transparent;
                color: var(--text-primary);
                padding: 80px 0 60px;
                margin-bottom: 40px;
                position: relative;
            }

            .hero h1 {
                font-weight: 800;
                background: linear-gradient(to right, #fff, #A1A1AA);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 20px;
            }

            .hero .lead {
                color: var(--text-secondary);
                font-size: 1.2rem;
            }

            .card {
                background: var(--glass-bg);
                border: var(--glass-border);
                border-radius: var(--radius-md);
                backdrop-filter: var(--backdrop-blur);
                box-shadow: var(--glass-shadow);
                margin-bottom: 24px;
            }

            .card-header {
                background: rgba(255, 255, 255, 0.02);
                border-bottom: var(--glass-border);
                padding: 20px;
            }

            .card-header h4, .card-header h5 {
                color: var(--text-primary);
                margin: 0;
                font-weight: 600;
            }

            .card-body {
                padding: 24px;
            }

            .form-control, .form-select {
                background: rgba(0, 0, 0, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: var(--text-primary);
                border-radius: 12px;
                padding: 12px 16px;
            }

            .form-control:focus, .form-select:focus {
                background: rgba(0, 0, 0, 0.4);
                border-color: var(--primary);
                box-shadow: 0 0 0 2px rgba(255, 107, 0, 0.2);
                color: var(--text-primary);
            }

            .form-label {
                color: var(--text-secondary);
                margin-bottom: 8px;
                font-weight: 500;
            }

            .btn-primary {
                background: var(--primary-gradient);
                border: none;
                border-radius: 12px;
                padding: 12px 24px;
                font-weight: 600;
                box-shadow: 0 4px 15px rgba(255, 107, 0, 0.3);
                transition: all 0.3s;
            }

            .btn-primary:hover {
                background: var(--primary-gradient);
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(255, 107, 0, 0.5);
            }

            .btn-light {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: var(--text-primary);
                border-radius: 12px;
                backdrop-filter: blur(10px);
            }

            .btn-light:hover {
                background: rgba(255, 255, 255, 0.2);
                color: var(--text-primary);
                border-color: rgba(255, 255, 255, 0.2);
            }

            .btn-outline-light {
                border-color: rgba(255, 255, 255, 0.2);
                color: var(--text-secondary);
                border-radius: 12px;
            }

            .btn-outline-light:hover {
                background: rgba(255, 255, 255, 0.1);
                border-color: var(--text-primary);
                color: var(--text-primary);
            }

            .result-area {
                min-height: 200px;
                background: rgba(0, 0, 0, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 12px;
                padding: 24px;
                color: var(--text-secondary);
            }

            .chat-area {
                min-height: 240px;
                max-height: 420px;
                overflow-y: auto;
                background: rgba(0, 0, 0, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 12px;
                padding: 16px;
                color: var(--text-secondary);
            }

            .message {
                display: block;
                padding: 8px 12px;
                border-radius: 12px;
                margin-bottom: 8px;
                max-width: 75%;
            }

            .message.user {
                background: rgba(255, 255, 255, 0.08);
                margin-left: auto;
                text-align: right;
                color: var(--text-primary);
            }

            .message.assistant {
                background: rgba(255, 255, 255, 0.05);
            }

            .message .meta {
                font-size: 12px;
                color: var(--text-secondary);
                margin-bottom: 4px;
            }

            .text-muted {
                color: var(--text-secondary) !important;
            }

            i {
                color: var(--primary);
            }

            .hero i.fa-robot {
                color: var(--text-secondary);
                opacity: 0.1 !important;
            }
        </style>
    </head>
    <body>
        <div class="background"></div>
        <div class="hero">
            <div class="container">
                <div class="row align-items-center">
                    <div class="col-md-8">
                        <h1>📄 办公智能体助手</h1>
                        <p class="lead">基于 LangGraph 1.0 的智能文档处理系统</p>
                        <p>支持文档总结、生成、转换，让AI成为你的办公助手</p>
                        <div class="mt-3">
                            <a href="/chat" class="btn btn-light btn-lg me-2">
                                <i class="fas fa-comments"></i> 对话模式
                            </a>
                            <a href="/command" class="btn btn-outline-light btn-lg">
                                <i class="fas fa-brain"></i> 指挥中心 🌟
                            </a>
                        </div>
                    </div>
                    <div class="col-md-4 text-center">
                        <i class="fas fa-robot fa-6x opacity-50"></i>
                    </div>
                </div>
            </div>
        </div>

        <div class="container">
            <div class="row">
                <div class="col-md-12">
                    <div class="card mb-4">
                        <div class="card-header">
                            <h4><i class="fas fa-comments"></i> 问答聊天</h4>
                        </div>
                        <div class="card-body">
                            <div id="chatArea" class="chat-area">
                                <p class="text-muted text-center">在这里和智能体进行对话</p>
                            </div>
                            <div class="mt-3 d-flex gap-2">
                                <input type="file" id="chatDoc" class="form-control" style="max-width:220px" accept=".txt,.pdf,.docx,.xlsx,.csv,.md,.json">
                                <textarea id="chatInput" class="form-control" rows="2" placeholder="请输入问题，支持 @智能体 提及..."></textarea>
                            </div>
                            <div class="mt-2 d-flex justify-content-end gap-2">
                                <button id="chatClearBtn" class="btn btn-outline-secondary btn-sm"><i class="fas fa-trash"></i> 清除</button>
                                <button id="chatSendBtn" class="btn btn-primary btn-sm"><i class="fas fa-paper-plane"></i> 发送</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <!-- 上传区域 -->
            <div class="row">
                <div class="col-md-12">
                    <div class="card mb-4">
                        <div class="card-header">
                            <h4><i class="fas fa-upload"></i> 上传文档</h4>
                        </div>
                        <div class="card-body">
                            <form id="uploadForm">
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="file" class="form-label">选择文件</label>
                                            <input type="file" class="form-control" id="file" name="file" required accept=".txt,.pdf,.docx,.xlsx,.csv,.md,.json">
                                            <div class="form-text">支持: TXT, PDF, DOCX, XLSX, CSV, MD, JSON</div>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="operation" class="form-label">操作类型</label>
                                            <select class="form-select" id="operation" name="operation" required>
                                                <option value="">请选择...</option>
                                                <option value="summarize">总结文档</option>
                                                <option value="generate">生成内容</option>
                                                <option value="convert">格式转换</option>
                                                <option value="extract_table">提取表格</option>
                                                <option value="extract_key_points">提取要点</option>
                                                <option value="analyze">深度分析</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>

                                <div class="row">
                                    <div class="col-md-12">
                                        <div class="mb-3">
                                            <label for="instruction" class="form-label">额外指示 <span class="text-muted">(可选)</span></label>
                                            <textarea class="form-control" id="instruction" name="instruction" rows="2" placeholder="例如：生成邮件格式，重点突出数据指标..."></textarea>
                                        </div>
                                    </div>
                                </div>

                                <button type="submit" class="btn btn-primary btn-lg w-100" id="submitBtn">
                                    <i class="fas fa-play"></i> 开始处理
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 状态和信息 -->
            <div class="row">
                <div class="col-md-4">
                    <div class="card mb-4">
                        <div class="card-header">
                            <h5><i class="fas fa-info-circle"></i> 文件信息</h5>
                        </div>
                        <div class="card-body">
                            <div id="fileInfo" class="file-info">
                                <p class="text-muted">等待上传文件...</p>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="col-md-4">
                    <div class="card mb-4">
                        <div class="card-header">
                            <h5><i class="fas fa-clock"></i> 处理状态</h5>
                        </div>
                        <div class="card-body">
                            <div id="statusInfo">
                                <p class="text-muted">等待开始处理...</p>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="col-md-4">
                    <div class="card mb-4">
                        <div class="card-header">
                            <h5><i class="fas fa-history"></i> 统计信息</h5>
                        </div>
                        <div class="card-body">
                            <div id="statsInfo">
                                <small>
                                    <div>已处理文件: <strong id="totalFiles">0</strong></div>
                                    <div>成功: <span class="text-success" id="successFiles">0</span></div>
                                    <div>需要审核: <span class="text-warning" id="reviewFiles">0</span></div>
                                    <div>失败: <span class="text-danger" id="failedFiles">0</span></div>
                                </small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 处理进度 -->
            <div class="row" id="progressRow" style="display: none;">
                <div class="col-md-12">
                    <div class="card mb-4">
                        <div class="card-body">
                            <div class="d-flex align-items-center">
                                <div class="spinner-border text-primary me-3" role="status">
                                    <span class="visually-hidden">处理中...</span>
                                </div>
                                <div>
                                    <strong id="progressText">正在处理...</strong>
                                    <div class="text-muted small" id="progressDetail"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 结果预览 -->
            <div class="row">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fas fa-file-alt"></i> 处理结果</h5>
                        </div>
                        <div class="card-body">
                            <div id="resultArea" class="result-area">
                                <p class="text-muted text-center">处理结果将在此显示...</p>
                            </div>
                        </div>
                        <div class="card-footer" id="resultFooter" style="display: none;">
                            <button class="btn btn-outline-secondary btn-sm" id="downloadBtn">
                                <i class="fas fa-download"></i> 下载结果
                            </button>
                            <button class="btn btn-outline-primary btn-sm" id="reviewBtn" style="display: none;">
                                <i class="fas fa-eye"></i> 需要审核
                            </button>
                            <button class="btn btn-outline-success btn-sm" id="continueWorkbenchBtn" style="display: none;">
                                <i class="fas fa-arrow-right"></i> 在工作台继续
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            const chatArea = document.getElementById('chatArea');
            const chatInput = document.getElementById('chatInput');
            const chatSendBtn = document.getElementById('chatSendBtn');
            const chatClearBtn = document.getElementById('chatClearBtn');
            const chatDocInput = document.getElementById('chatDoc');
            function appendMessage(role, text, agent) {
                const div = document.createElement('div');
                div.className = `message ${role}`;
                const meta = document.createElement('div');
                meta.className = 'meta';
                meta.textContent = role === 'user' ? '你' : (agent ? `${agent}` : '助手');
                const body = document.createElement('div');
                body.innerText = text;
                div.appendChild(meta);
                div.appendChild(body);
                chatArea.appendChild(div);
                chatArea.scrollTop = chatArea.scrollHeight;
            }
            async function sendChat() {
                const text = chatInput.value.trim();
                if (!text) return;
                appendMessage('user', text);
                chatSendBtn.disabled = true;
                const formData = new FormData();
                formData.append('message', text);
                if (chatDocInput.files && chatDocInput.files[0]) {
                    formData.append('document', chatDocInput.files[0]);
                }
                try {
                    const res = await fetch('/api/chat', { method: 'POST', body: formData });
                    const data = await res.json();
                    const agentName = data.agent && data.agent.name ? data.agent.name : '';
                    const agentEmoji = data.agent && data.agent.emoji ? data.agent.emoji : '';
                    const tag = agentEmoji && agentName ? `${agentEmoji} ${agentName}` : (agentName || '助手');
                    appendMessage('assistant', data.response || '', tag);
                } catch (e) {
                    appendMessage('assistant', '请求失败');
                } finally {
                    chatSendBtn.disabled = false;
                    chatInput.value = '';
                    chatDocInput.value = '';
                }
            }
            chatSendBtn.addEventListener('click', sendChat);
            chatInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendChat();
                }
            });
            chatClearBtn.addEventListener('click', async function() {
                try {
                    await fetch('/api/chat/clear', { method: 'POST' });
                } catch (e) {}
                chatArea.innerHTML = '<p class="text-muted text-center">在这里和智能体进行对话</p>';
            });
            // 文件信息更新
            document.getElementById('file').addEventListener('change', function(e) {
                const file = e.target.files[0];
                if (file) {
                    const fileInfo = `
                        <strong>文件名:</strong> ${file.name}<br>
                        <strong>大小:</strong> ${(file.size / 1024 / 1024).toFixed(2)} MB<br>
                        <strong>类型:</strong> ${file.name.split('.').pop().toUpperCase()}
                    `;
                    document.getElementById('fileInfo').innerHTML = fileInfo;
                }
            });

            // 表单提交
            document.getElementById('uploadForm').addEventListener('submit', async function(e) {
                e.preventDefault();

                const formData = new FormData(this);
                const submitBtn = document.getElementById('submitBtn');
                const progressRow = document.getElementById('progressRow');
                const resultArea = document.getElementById('resultArea');
                const statusInfo = document.getElementById('statusInfo');

                // 重置UI
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 处理中...';
                progressRow.style.display = 'block';
                resultArea.innerHTML = '<p class="text-center text-muted"><i class="fas fa-cog fa-spin"></i> 正在处理文档，请稍候...</p>';
                statusInfo.innerHTML = '<p class="text-info">正在上传文件...</p>';

                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });

                    const result = await response.json();

                    if (result.success) {
                        statusInfo.innerHTML = `<p class="text-success"><i class="fas fa-check-circle"></i> ${result.message}</p>`;
                        resultArea.innerHTML = `<pre class="border-0 bg-light p-3 rounded">${result.result_preview}</pre>`;

                        // 显示下载按钮
                        document.getElementById('resultFooter').style.display = 'block';
                        document.getElementById('downloadBtn').setAttribute('data-filename', result.output_file);

                        // 如果需要审核
                        if (result.needs_review) {
                            document.getElementById('reviewBtn').style.display = 'inline-block';
                        }

                        const op = (result.metadata && result.metadata.operation) || '';
                        const len = (result.metadata && result.metadata.result_length) || 0;
                        const isHeavy = !!result.needs_review || ['generate', 'analyze'].includes(op) && len >= 3000;
                        if (isHeavy) {
                            const btn = document.getElementById('continueWorkbenchBtn');
                            btn.style.display = 'inline-block';
                            btn.setAttribute('data-operation', op);
                        }

                        // 更新统计
                        updateStats(result);
                    } else {
                        throw new Error(result.error || '处理失败');
                    }
                } catch (error) {
                    console.error('Error:', error);
                    statusInfo.innerHTML = `<p class="text-danger"><i class="fas fa-times-circle"></i> 错误: ${error.message}</p>`;
                    resultArea.innerHTML = `<div class="alert alert-danger">处理失败: ${error.message}</div>`;
                } finally {
                    progressRow.style.display = 'none';
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<i class="fas fa-play"></i> 开始处理';
                }
            });

            // 下载按钮
            document.getElementById('downloadBtn').addEventListener('click', function() {
                const filename = this.getAttribute('data-filename');
                if (filename) {
                    window.location.href = `/download/${filename}`;
                }
            });

            // 审核按钮
            document.getElementById('reviewBtn').addEventListener('click', function() {
                alert('审核功能需要在实际应用中集成审核系统。当前为演示版本。');
            });

            document.getElementById('continueWorkbenchBtn').addEventListener('click', function() {
                const op = this.getAttribute('data-operation') || '';
                const url = op ? `/command?from=home&operation=${encodeURIComponent(op)}` : '/command?from=home';
                window.location.href = url;
            });

            // 更新统计
            function updateStats(result) {
                const totalEl = document.getElementById('totalFiles');
                const successEl = document.getElementById('successFiles');
                const reviewEl = document.getElementById('reviewFiles');
                const failedEl = document.getElementById('failedFiles');

                totalEl.textContent = parseInt(totalEl.textContent) + 1;

                if (result.success) {
                    successEl.textContent = parseInt(successEl.textContent) + 1;
                    if (result.needs_review) {
                        reviewEl.textContent = parseInt(reviewEl.textContent) + 1;
                    }
                } else {
                    failedEl.textContent = parseInt(failedEl.textContent) + 1;
                }
            }
        </script>
    </body>
    </html>
    """

    return templates.TemplateResponse("command_center_v2.html", {"request": request})


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    operation: Optional[str] = Form(...),
    instruction: Optional[str] = Form("")
):
    """上传文件并处理"""
    # 验证操作类型
    valid_operations = ["summarize", "generate", "convert", "extract_table", "extract_key_points", "analyze"]
    if operation not in valid_operations:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": f"无效的操作类型。支持的操作: {', '.join(valid_operations)}"
            }
        )

    # 检查文件大小 (最大 50MB)
    file_size = 0
    file_content = await file.read()
    file_size = len(file_content)
    await file.seek(0)  # 重置文件指针

    if file_size > 50 * 1024 * 1024:
        return JSONResponse(
            status_code=413,
            content={
                "success": False,
                "error": "文件太大，最大支持 50MB"
            }
        )

    # 保存上传的文件
    file_ext = os.path.splitext(file.filename)[1].lower()
    unique_id = str(uuid.uuid4())[:8]
    file_path = os.path.join(UPLOAD_DIR, f"{unique_id}_{file.filename}")

    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # 使用 LangGraph 处理
        print(f"\n{'='*60}")
        print(f"开始处理文件: {file.filename}")
        print(f"操作类型: {operation}")
        print(f"保存路径: {file_path}")
        print(f"{'='*60}\n")

        result = process_document(
            file_path=file_path,
            operation=operation,
            instruction=instruction,
            original_filename=file.filename
        )

        if result.get('error'):
            return {
                "success": False,
                "error": result['error'],
                "file_info": get_file_info(file_path)
            }

        # 获取输出文件名
        output_file = None
        result_preview = None
        needs_review = False
        metadata = result.get('metadata') or {}
        processing_time = metadata.get('processing_time', 'N/A') if metadata else 'N/A'

        if metadata and 'output_file' in metadata:
            output_file = metadata['output_file']

        if result['result']:
            preview_length = min(2000, len(result['result']))
            result_preview = result['result'][:preview_length]
            needs_review = len(result['result']) > 3000

            # 如果需要审核，标记
            if result['needs_review']:
                result_preview = f"⚠️ 检测到内容长度较大，建议人工审核\n\n=== 预览 ===\n\n{result_preview}"

        return {
            "success": True,
            "message": f"处理完成 (耗时: {processing_time})",
            "file_info": get_file_info(file_path),
            "result_preview": result_preview,
            "output_file": output_file,
            "needs_review": needs_review,
            "metadata": metadata
        }

    except Exception as e:
        print(f"处理失败: {e}")
        import traceback
        traceback.print_exc()

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"处理失败: {str(e)}"
            }
        )

    finally:
        # 清理原始文件（保留处理结果）
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass


@app.get("/download/{filename}")
async def download_file(filename: str, preview: bool = False):
    """下载结果文件"""
    file_path = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    # 确定媒体类型
    media_types = {
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".json": "application/json",
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }

    ext = os.path.splitext(filename)[1].lower()
    media_type = media_types.get(ext, "application/octet-stream")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type,
        content_disposition_type="inline" if preview else "attachment"
    )


@app.get("/supported-formats")
async def get_supported_formats():
    """获取支持的文件格式"""
    return {
        "success": True,
        "formats": list_supported_formats()
    }


@app.get("/recent-files")
async def get_recent_files():
    """获取最近的处理文件列表"""
    try:
        files = []
        if os.path.exists(UPLOAD_DIR):
            for filename in os.listdir(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, filename)
                if os.path.isfile(file_path) and "result" in filename:
                    stat = os.stat(file_path)
                    files.append({
                        "filename": filename,
                        "size": stat.st_size,
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    })

        # 按修改时间排序
        files.sort(key=lambda x: x['modified'], reverse=True)
        files = files[:20]  # 只显示最近20个

        return {
            "success": True,
            "files": files
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )


@app.get("/api/files")
async def list_files():
    """获取所有文件列表"""
    try:
        files = []
        if os.path.exists(UPLOAD_DIR):
            for filename in os.listdir(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, filename)
                if os.path.isfile(file_path) and not filename.startswith('.'):
                    stat = os.stat(file_path)
                    ext = os.path.splitext(filename)[1].lower()
                    files.append({
                        "name": filename,
                        "size": stat.st_size,
                        "size_formatted": f"{stat.st_size / 1024:.1f} KB" if stat.st_size < 1024 * 1024 else f"{stat.st_size / (1024 * 1024):.1f} MB",
                        "type": ext,
                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                        "timestamp": stat.st_mtime
                    })
        
        # Sort by modification time desc
        files.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            "success": True,
            "files": files
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )


@app.post("/api/upload/simple")
async def simple_upload(file: UploadFile = File(...)):
    """仅上传文件，不进行处理"""
    try:
        unique_id = str(uuid.uuid4())[:8]
        file_path = os.path.join(UPLOAD_DIR, f"{unique_id}_{file.filename}")
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
            
        return {
            "success": True,
            "message": "文件上传成功",
            "filename": f"{unique_id}_{file.filename}"
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


@app.delete("/api/files/{filename}")
async def delete_file(filename: str):
    """删除指定文件"""
    try:
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            os.remove(file_path)
            return {
                "success": True,
                "message": f"文件 {filename} 已删除"
            }
        else:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error": "文件不存在"
                }
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )


@app.delete("/clear-uploads")
async def clear_uploads():
    """清理上传目录"""
    try:
        count = 0
        if os.path.exists(UPLOAD_DIR):
            for filename in os.listdir(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    count += 1

        return {
            "success": True,
            "message": f"已清理 {count} 个文件"
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )


# 健康检查接口
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "office-assistant"
    }


# API 信息
@app.get("/api/info")
async def api_info():
    """API信息"""
    return {
        "service": "办公智能体助手 (LangGraph 1.0)",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/upload (POST) - 上传并处理文档",
            "download": "/download/{filename} (GET) - 下载结果",
            "health": "/health (GET) - 健康检查",
            "formats": "/supported-formats (GET) - 支持格式",
            "chat": "/chat (GET) - 多智能体聊天界面",
            "api_chat": "/api/chat (POST) - 聊天API",
            "api_agents": "/api/agents (GET) - 智能体列表"
        },
        "features": [
            "文档总结",
            "内容生成",
            "格式转换",
            "表格提取",
            "要点提取",
            "深度分析",
            "多智能体协作",
            "对话式交互"
        ]
    }


class ModelSettings(BaseModel):
    provider: str
    api_key: str
    model_name: Optional[str] = None
    base_url: Optional[str] = None
    temperature: Optional[float] = 0.3


@app.post("/api/settings/model")
async def update_model_settings(settings: ModelSettings):
    """更新模型配置"""
    try:
        # Update environment variables
        os.environ["LLM_PROVIDER"] = settings.provider
        os.environ["LLM_API_KEY"] = settings.api_key
        
        if settings.model_name:
            os.environ["LLM_MODEL_NAME"] = settings.model_name
        
        if settings.base_url:
            os.environ["LLM_BASE_URL"] = settings.base_url
            
        # Backward compatibility for Gemini specific env vars
        if settings.provider == "gemini":
            os.environ["GEMINI_API_KEY"] = settings.api_key
            if settings.model_name:
                os.environ["GEMINI_MODEL"] = settings.model_name

        # Reload agents
        multi_agent_system.reload_agents()
        
        return {
            "success": True,
            "message": f"已切换到 {settings.provider} 模型 ({settings.model_name or '默认'})"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )


@app.get("/api/settings/model")
async def get_model_settings():
    """获取当前模型配置"""
    try:
        provider = os.getenv("LLM_PROVIDER", "gemini")
        api_key = os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY", "")
        model_name = os.getenv("LLM_MODEL_NAME") or os.getenv("GEMINI_MODEL", "")
        base_url = os.getenv("LLM_BASE_URL", "")
        
        return {
            "success": True,
            "settings": {
                "provider": provider,
                "api_key": api_key,
                "model_name": model_name,
                "base_url": base_url
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )




# ==================== 多智能体聊天功能 ====================

@app.get("/chat", response_class=HTMLResponse)
async def chat_page():
    """多智能体聊天页面重定向到指挥中心"""
    return RedirectResponse(url="/")


@app.get("/command", response_class=HTMLResponse)
async def command_center(request: Request):
    """智能体指挥中心"""
    return templates.TemplateResponse("command_center_v2.html", {"request": request})


@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page():
    """数据分析仪表盘重定向到指挥中心"""
    return RedirectResponse(url="/")


@app.get("/api/analytics/data")
async def get_analytics_data():
    """获取分析数据（模拟）"""
    return {
        "success": True,
        "kpi": {
            "docs": 1284,
            "calls": 5432,
            "time": 1.2,
            "health": 100
        },
        "trend": [120, 200, 150, 80, 70, 110, 130],
        "distribution": [
            {"value": 1048, "name": "PDF"},
            {"value": 735, "name": "Word"},
            {"value": 580, "name": "Excel"},
            {"value": 484, "name": "TXT"}
        ],
        "activity": [120, 200, 150, 80, 70]
    }


@app.get("/api/agents")
async def get_agents():
    """获取所有智能体列表"""
    try:
        agents = multi_agent_system.registry.get_agent_info()
        return {
            "success": True,
            "agents": agents
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )


@app.post("/api/chat")
async def chat_with_agent(
    message: str = Form(...),
    document: Optional[UploadFile] = File(None),
    document_text: Optional[str] = Form(None),
    filename: Optional[str] = Form(None),
    scenario: Optional[str] = Form(None),
    agent_id: Optional[str] = Form(None)
):
    """与智能体对话"""
    try:
        # 处理文档（如果有）
        document_content = None
        
        if document:
            # 保存上传的文档
            file_ext = os.path.splitext(document.filename)[1].lower()
            unique_id = str(uuid.uuid4())[:8]
            file_path = os.path.join(UPLOAD_DIR, f"{unique_id}_{document.filename}")
            
            with open(file_path, "wb") as f:
                content = await document.read()
                f.write(content)
            
            # 读取文档内容
            try:
                file_type = detect_file_type(file_path)
                document_content = read_file(file_path, file_type)
                print(f"✅ 文档读取成功: {document.filename}")
                print(f"   文件类型: {file_type}")
                print(f"   内容长度: {len(document_content) if document_content else 0} 字符")
                if document_content:
                    print(f"   内容预览: {document_content[:200]}...")
            except Exception as e:
                print(f"❌ 读取文档失败: {e}")
                import traceback
                traceback.print_exc()
            finally:
                # 清理临时文件
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        pass
        
        elif filename:
            # 从现有文件读取
            file_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.exists(file_path):
                try:
                    file_type = detect_file_type(file_path)
                    document_content = read_file(file_path, file_type)
                    print(f"📂 读取现有文件: {filename}")
                    print(f"   文件类型: {file_type}")
                    print(f"   内容长度: {len(document_content) if document_content else 0} 字符")
                except Exception as e:
                    print(f"❌ 读取文件失败: {e}")
            else:
                print(f"⚠️ 文件不存在: {filename}")
        
        elif document_text:
            document_content = document_text
            print(f"📝 使用文本内容: {len(document_text) if document_text else 0} 字符")
        
        # 调用多智能体系统
        print(f"🤖 调用多智能体系统...")
        print(f"   消息: {message}")
        print(f"   场景: {scenario}")
        print(f"   有文档内容: {document_content is not None}")

        if agent_id:
            try:
                agent_obj = multi_agent_system.registry.get(agent_id)
            except Exception:
                agent_obj = None
            if agent_obj:
                message = f"@{agent_obj.name} {message}"
        
        # Special handling for Compliance Scenario (respect explicit @mentions)
        try:
            explicit_mentions = multi_agent_system.router.parse_mentions(message)
        except Exception:
            explicit_mentions = []

        if scenario == 'compliance' and not document_content and not explicit_mentions:
            print("⚖️ 触发合规营销工作流...")
            result = run_compliance_flow(message)

            final_content = result.get('content', '')
            review_result = result.get('review_result', '')
            status = result.get('status', '')

            response_text = f"""**合规营销文案生成报告**

**最终状态**: {status}
**迭代次数**: {result.get('iteration_count')}

---
**最终文案**:
{final_content}

---
**合规审核意见**:
{review_result}
"""
            return {
                "success": True,
                "agent": {
                    "name": "合规官",
                    "role": "流程负责人",
                    "emoji": "fas fa-balance-scale"
                },
                "response": response_text,
                "routing_info": {
                    "type": "workflow",
                    "reason": "执行了合规营销工作流"
                }
            }

        result = multi_agent_system.chat(message, document_content, scenario)
        
        print(f"[聊天API] multi_agent_system.chat 返回结果:")
        print(f"  success: {result.get('success')}")
        print(f"  agent: {result.get('agent')}")
        print(f"  response 长度: {len(str(result.get('response', '')))}")
        print(f"  response 前100字符: {str(result.get('response', ''))[:100]}")
        
        if result["success"]:
            response_data = {
                "success": True,
                "agent": result.get("agent", {}),
                "response": result.get("response", ""),
                "routing_info": result.get("routing_info", {})
            }
            print(f"[聊天API] 返回数据: success={response_data['success']}, agent={response_data.get('agent', {}).get('name', 'N/A')}, response长度={len(str(response_data['response']))}")
            return response_data
        else:
            error_msg = result.get("error", "处理失败")
            print(f"[聊天API] 返回错误: {error_msg}")
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": error_msg
                }
            )
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"处理失败: {str(e)}"
            }
        )


@app.post("/api/image/generate")
async def generate_image(
    prompt: str = Form(...),
    model: Optional[str] = Form("nano-banana-pro"),
    size: Optional[str] = Form("1024x1024")
):
    try:
        agent = multi_agent_system.registry.get("图像生成专家")
        if not agent:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "图像生成专家未注册"}
            )
        data = agent._gen_via_api(prompt, model=model, size=size)
        if not data.get("success"):
            return {
                "success": False,
                "error": data.get("error", "生成失败"),
                "hint": data.get("hint")
            }
        d = data.get("data", {})
        html = None
        url = None
        image_base64 = None
        if isinstance(d, dict) and d.get("image_base64"):
            image_base64 = d["image_base64"]
            html = f"<img src=\"data:image/png;base64,{image_base64}\" style=\"max-width:100%\"/>"
        elif isinstance(d, dict) and d.get("url"):
            url = d["url"]
            html = f"<img src=\"{url}\" style=\"max-width:100%\"/>"
        else:
            html = json.dumps(d, ensure_ascii=False)
        return {
            "success": True,
            "agent": {
                "id": "image_generator",
                "name": "图像生成专家",
                "role": "图像生成与编辑",
                "emoji": "fas fa-image"
            },
            "html": html,
            "url": url,
            "image_base64": image_base64
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/api/draw/generate")
async def draw_generate(
    prompt: str = Form(...),
    tools: Optional[str] = Form(None)
):
    try:
        agent = multi_agent_system.registry.get("绘画智能体")
        if not agent:
            return JSONResponse(status_code=404, content={"success": False, "error": "绘画智能体未注册"})
        tool_list = []
        if tools:
            tool_list = [t.strip() for t in tools.split(",") if t.strip()]
        results = agent.generate_images(prompt, tool_list)
        items = []
        for r in results:
            if r.get("image_base64"):
                b64 = r["image_base64"]
                mime = r.get("mime", "image/png")
                ext = "svg" if "svg" in mime else ("png" if "png" in mime else "png")
                tool_name = r.get('tool', 'unknown')
                source_code = r.get('source_code', '')
                
                # 如果有源代码，显示可展开的代码块
                code_section = ""
                if source_code:
                    code_section = f"""<details style="margin-top: 8px; padding: 8px; background: rgba(0,0,0,0.2); border-radius: 6px;">
                        <summary style="cursor: pointer; color: var(--text-secondary); font-size: 0.85rem;">查看源代码</summary>
                        <pre style="margin-top: 8px; padding: 10px; background: #1e1e1e; border-radius: 4px; overflow-x: auto; font-size: 0.75rem; color: #d4d4d4;"><code>{source_code}</code></pre>
                    </details>"""
                
                # 优化样式：添加白色背景以适配深色模式，添加 padding 防止贴边，max-height 防止过高
                items.append(f"""<div style="border:1px solid var(--border); border-radius:12px; overflow:hidden; background: var(--glass-bg);">
                    <div style="padding:8px; font-weight:600; border-bottom:1px solid var(--border);">{tool_name}</div>
                    <div style="background-color: white; padding: 10px; display: flex; justify-content: center; align-items: center; min-height: 200px;">
                        <img src="data:{mime};base64,{b64}" style="max-width:100%; height:auto; display:block; box-shadow: 0 2px 10px rgba(0,0,0,0.1);"/>
                    </div>
                    <div style="padding:8px;">
                        <a download="{tool_name}.{ext}" href="data:{mime};base64,{b64}" style="color: var(--primary); text-decoration: none;">
                            <i class="fas fa-download"></i> 下载图片
                        </a>
                    </div>
                    {code_section}
                </div>""")
            else:
                err = r.get("error") or "生成失败"
                hint = r.get("hint")
                items.append(f"<div style=\"border:1px dashed var(--border); border-radius:12px; padding:12px; color:var(--text-secondary);\">{r.get('tool')}：{err}{('，' + hint) if hint else ''}</div>")
        grid = f"<div style=\"display:grid; grid-template-columns: repeat(auto-fit, minmax(220px,1fr)); gap:12px;\">{''.join(items)}</div>"
        # 这里添加一个重新生成按钮，调用前端的 runDrawingGenerator()
        grid += """
        <div style="margin-top: 16px; text-align: center;">
            <button onclick="runDrawingGenerator()" class="btn btn-primary btn-sm">
                <i class="fas fa-redo"></i> 重新生成
            </button>
        </div>
        """
        return {"success": True, "html": grid, "results": results}
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@app.post("/api/chat/clear")
async def clear_chat():
    """清除对话历史"""
    try:
        multi_agent_system.clear_conversation()
        return {
            "success": True,
            "message": "对话已清除"
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )


@app.get("/api/chat/history")
async def get_chat_history():
    """获取对话历史"""
    try:
        history = multi_agent_system.get_conversation_history()
        return {
            "success": True,
            "history": history
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )


# ==================== 向量存储 API ====================
from tools.vector_store import vector_store_manager


@app.post("/api/knowledge/add")
async def add_to_knowledge_base(file: UploadFile = File(...)):
    """
    将文档添加到知识库（向量化存储）
    """
    try:
        # 保存文件
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 添加到向量存储
        result = vector_store_manager.add_document(
            file_path,
            metadata={
                "filename": file.filename,
                "upload_time": datetime.now().isoformat()
            }
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": "文档已添加到知识库",
                "doc_id": result["doc_id"],
                "chunks_count": result["chunks_count"]
            }
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": result["error"]
                }
            )
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )


@app.post("/api/knowledge/search")
async def search_knowledge_base(
    query: str = Form(...),
    k: int = Form(5)
):
    """
    搜索知识库
    """
    try:
        results = vector_store_manager.search(query, k=k)
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "count": len(results)
        }
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )


@app.get("/api/knowledge/list")
async def list_knowledge_base():
    """
    列出知识库中的所有文档
    """
    try:
        documents = vector_store_manager.list_documents()
        
        return {
            "success": True,
            "documents": documents,
            "count": len(documents)
        }
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )


@app.delete("/api/knowledge/{doc_id}")
async def delete_from_knowledge_base(doc_id: str):
    """
    从知识库中删除文档
    """
    try:
        success = vector_store_manager.delete_document(doc_id)
        
        if success:
            return {
                "success": True,
                "message": "文档已从知识库删除"
            }
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "删除失败"
                }
            )
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )


@app.get("/api/knowledge/{doc_id}")
async def get_document_from_knowledge_base(doc_id: str):
    """
    获取知识库中的文档详情
    """
    try:
        chunks = vector_store_manager.get_document_by_id(doc_id)
        
        if chunks:
            return {
                "success": True,
                "doc_id": doc_id,
                "chunks": chunks,
                "total_chunks": len(chunks)
            }
        else:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error": "文档未找到"
                }
            )
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )


# ================= Prompt Agent API =================

@app.post("/api/prompt/optimize")
async def optimize_prompt_api(
    prompt: str = Form(...),
    model: str = Form("general"),
    framework: str = Form("auto"),
    tone: str = Form("professional")
):
    """优化提示词"""
    try:
        result = await prompt_manager.optimize_prompt(prompt, model, framework, tone)
        # Check if it's a dict or string (backward compatibility check, though we updated manager)
        if isinstance(result, dict):
            return {"success": True, "data": result}
        else:
            return {"success": True, "data": {"optimized_prompt": result, "explanation": "无详细说明", "comparison": "无"}}
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@app.get("/api/prompt/library")
async def list_prompts_api():
    """获取提示词库"""
    try:
        prompts = prompt_manager.list_prompts()
        return {"success": True, "prompts": prompts}
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@app.post("/api/prompt/library")
async def save_prompt_api(
    title: str = Form(...),
    content: str = Form(...),
    tags: str = Form("")
):
    """保存提示词"""
    try:
        tags_list = [t.strip() for t in tags.split(",") if t.strip()]
        new_prompt = prompt_manager.save_prompt(title, content, tags_list)
        return {"success": True, "prompt": new_prompt}
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@app.delete("/api/prompt/library/{prompt_id}")
async def delete_prompt_api(prompt_id: str):
    """删除提示词"""
    try:
        success = prompt_manager.delete_prompt(prompt_id)
        return {"success": success}
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@app.get("/api/prompt/best-practices")
async def get_best_practices_api():
    """获取最佳实践"""
    return {"success": True, "practices": prompt_manager.get_best_practices()}


# ================= Workflow API =================

@app.post("/api/workflow/review")
async def workflow_document_review(
    file: UploadFile = File(...),
    instruction: Optional[str] = Form(None)
):
    """
    [工作流] 智能文档多维审查
    流程: 文档分析师 (摘要) + 合规官 (风险) -> 内容创作者 (汇总报告)
    """
    try:
        # 1. 保存文件
        file_ext = os.path.splitext(file.filename)[1].lower()
        unique_id = str(uuid.uuid4())[:8]
        file_path = os.path.join(UPLOAD_DIR, f"review_{unique_id}_{file.filename}")
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
            
        # 2. 读取内容
        file_type = detect_file_type(file_path)
        doc_content = read_file(file_path, file_type)
        if len(doc_content) > 50000: # 简单截断防止过长
            doc_content = doc_content[:50000]
            
        # 3. 编排 Agent
        
        # Step 1: 平行执行 (Analyst & Compliance)
        # 由于当前是同步调用，我们按顺序执行
        
        # 3.1 文档分析师
        analyst = multi_agent_system.registry.get("文档分析师")
        analyst_prompt = f"""请仔细阅读以下文档，提取核心摘要和关键事实。
        
        文档内容:
        {doc_content[:10000]}... (略)
        """
        analyst_result = analyst.invoke([HumanMessage(content=analyst_prompt)])
        
        # 提取文本内容 - Agent 可能直接返回列表
        if isinstance(analyst_result, list):
            text_parts = []
            for item in analyst_result:
                if isinstance(item, dict) and 'text' in item:
                    text_parts.append(item['text'])
                elif isinstance(item, str):
                    text_parts.append(item)
                else:
                    text_parts.append(str(item))
            analyst_text = "\n".join(text_parts)
        elif hasattr(analyst_result, 'content'):
            content = analyst_result.content
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and 'text' in item:
                        text_parts.append(item['text'])
                    elif isinstance(item, str):
                        text_parts.append(item)
                    else:
                        text_parts.append(str(item))
                analyst_text = "\n".join(text_parts)
            elif isinstance(content, str):
                analyst_text = content
            else:
                analyst_text = str(content)
        else:
            analyst_text = str(analyst_result)
        
        print(f"[审查工作流] 文档分析师完成，输出长度: {len(analyst_text)}")
        
        # 3.2 合规官
        compliance = multi_agent_system.registry.get("合规官")
        compliance_prompt = f"""请作为合规官审查以下文档，指出潜在的风险点、合规漏洞或不当表述。
        
        文档内容:
        {doc_content[:10000]}... (略)
        """
        compliance_result = compliance.invoke([HumanMessage(content=compliance_prompt)])
        # 提取文本内容 - Agent 可能直接返回列表
        if isinstance(compliance_result, list):
            text_parts = []
            for item in compliance_result:
                if isinstance(item, dict) and 'text' in item:
                    text_parts.append(item['text'])
                elif isinstance(item, str):
                    text_parts.append(item)
                else:
                    text_parts.append(str(item))
            compliance_text = "\n".join(text_parts)
        elif hasattr(compliance_result, 'content'):
            content = compliance_result.content
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and 'text' in item:
                        text_parts.append(item['text'])
                    elif isinstance(item, str):
                        text_parts.append(item)
                    else:
                        text_parts.append(str(item))
                compliance_text = "\n".join(text_parts)
            elif isinstance(content, str):
                compliance_text = content
            else:
                compliance_text = str(content)
        else:
            compliance_text = str(compliance_result)
        
        print(f"[审查工作流] 合规官完成，输出长度: {len(compliance_text)}")
        
        # Step 2: 汇总 (Creator)
        
        # 3.3 内容创作者
        creator = multi_agent_system.registry.get("内容创作者")
        creator_prompt = f"""请根据以下两份分析报告，撰写一份《智能文档多维审查报告》。
        
        【分析师摘要】
        {analyst_text}
        
        【合规审查意见】
        {compliance_text}
        
        【输出要求】
        1. 标题：智能文档审查报告 - {file.filename}
        2. 结构：
           - 核心摘要 (基于分析师内容)
           - 风险提示 (基于合规官内容，高亮显示)
           - 综合建议
        3. 语气：专业、客观、严谨
        """
        final_report = creator.invoke([HumanMessage(content=creator_prompt)])
        # 提取文本内容 - Agent 可能直接返回列表
        if isinstance(final_report, list):
            text_parts = []
            for item in final_report:
                if isinstance(item, dict) and 'text' in item:
                    text_parts.append(item['text'])
                elif isinstance(item, str):
                    text_parts.append(item)
                else:
                    text_parts.append(str(item))
            final_text = "\n".join(text_parts)
        elif hasattr(final_report, 'content'):
            content = final_report.content
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and 'text' in item:
                        text_parts.append(item['text'])
                    elif isinstance(item, str):
                        text_parts.append(item)
                    else:
                        text_parts.append(str(item))
                final_text = "\n".join(text_parts)
            elif isinstance(content, str):
                final_text = content
            else:
                final_text = str(content)
        else:
            final_text = str(final_report)
        
        print(f"[审查工作流] 内容创作者完成，输出长度: {len(final_text)}")
        print(f"[审查工作流] 内容创作者前100字符: {final_text[:100]}")
        
        return {
            "success": True,
            "report": final_text,
            "steps": [
                {"agent": "文档分析师", "output": analyst_text},
                {"agent": "合规官", "output": compliance_text},
                {"agent": "内容创作者", "output": final_text}
            ]
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})
    finally:
        # Cleanup
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass


@app.post("/api/workflow/daily_tech")
async def workflow_daily_tech(
    request: Request,
    keywords: Optional[str] = Form(None),
    days: Optional[int] = Form(1),
    need_en: Optional[bool] = Form(False)
):
    try:
        kw_list: List[str] = []
        if keywords:
            kw_list = [k.strip() for k in keywords.split(',') if k.strip()]
        else:
            try:
                payload = await request.json()
                kws = payload.get('keywords') or ''
                if isinstance(kws, list):
                    kw_list = [str(k).strip() for k in kws if str(k).strip()]
                elif isinstance(kws, str):
                    kw_list = [k.strip() for k in kws.split(',') if k.strip()]
                days = payload.get('days', days or 1)
                need_en = bool(payload.get('need_en', need_en or False))
            except:
                pass
        if not kw_list:
            kw_list = ["人工智能", "芯片", "机器人"]
        result = run_daily_tech_flow(kw_list, int(days or 1), bool(need_en or False))
        report = result.get('translated') or result.get('report') or ''
        steps = [
            {"step": "collect", "output": result.get('raw_feed')},
            {"step": "cluster", "output": result.get('clusters')},
            {"step": "summarize", "output": result.get('summary')},
            {"step": "visualize", "output": result.get('charts')},
            {"step": "write", "output": result.get('report')},
        ]
        return {
            "success": True,
            "report": report,
            "steps": steps,
            "meta": {
                "keywords": kw_list,
                "days": int(days or 1),
                "need_en": bool(need_en or False),
                "report_date": result.get('report_date')
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


@app.post("/api/compose/contest")
async def compose_contest(
    file_path: Optional[str] = Form(None),
    project_name: Optional[str] = Form("AgentDesk 办公智能体工作台"),
    extra_notes: Optional[str] = Form(None),
    output_format: Optional[str] = Form("md")
):
    try:
        if not file_path:
            return JSONResponse(status_code=400, content={"success": False, "error": "缺少文件路径"})
        if not os.path.exists(file_path):
            return JSONResponse(status_code=404, content={"success": False, "error": "文件不存在"})
        ft = detect_file_type(file_path)
        content = read_file(file_path, ft)
        if not content:
            return JSONResponse(status_code=500, content={"success": False, "error": "读取失败或内容为空"})
        base_text = content[:20000]
        analyst = multi_agent_system.registry.get("文档分析师")
        analyst_prompt = f"""请提取以下文档的版式与章节结构要点，并输出JSON蓝图：
字段: title, sections[]，每个section包含: name, level(1-3), order, notes。
文档：
{base_text}
"""
        blueprint = analyst.invoke([HumanMessage(content=analyst_prompt)])
        creator = multi_agent_system.registry.get("内容创作者")
        creator_prompt = f"""基于以下结构蓝图，撰写参赛作品《{project_name}》。
要求：
1. 完全遵循蓝图的章节层级、编号与版式；
2. 内容围绕多智能体工作流、LangGraph编排、行业应用场景、技术架构、演示与可视化、落地与价值；
3. 语言专业、客观、清晰，适配评审阅读；
4. 每个章节提供要点条目与简明论述，长度与原版式相当；
5. 如蓝图包含表格或列表，按Markdown表格或有序列表输出；
6. 适当加入 Mermaid 流程图代码块展示关键流程；
补充说明：{extra_notes or ''}

结构蓝图：
{blueprint}
"""
        result_text = creator.invoke([HumanMessage(content=creator_prompt)])

        output_file = None
        download_url = None
        if (output_format or "md").lower() == "docx":
            unique_id = str(uuid.uuid4())[:8]
            filename = f"contest_{unique_id}.docx"
            output_path = os.path.join(UPLOAD_DIR, filename)
            try:
                markdown_to_docx(result_text, output_path)
                output_file = filename
                download_url = f"/download/{filename}"
            except Exception as e:
                print(f"❌ DOCX 导出失败: {e}")

        return {
            "success": True,
            "blueprint": blueprint,
            "content": result_text,
            "output_file": output_file,
            "download_url": download_url
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

if __name__ == "__main__":
    import uvicorn

    # 检查 Gemini API 密钥
    if not os.environ.get("GEMINI_API_KEY"):
        print("⚠️  警告: 未设置 GEMINI_API_KEY 环境变量")
        print("请在启动前设置: export GEMINI_API_KEY='your-api-key'\n")
        print("或者创建 .env 文件并填入配置\n")
        print("提示: 复制 .env.example 为 .env 并填写你的 Gemini API 密钥\n")
        print("="*60)
        print("配置示例:")
        print("  GEMINI_API_KEY=AIzaxxxxxxxxxxxxxx")
        print("  GEMINI_MODEL=gemini-3-pro-preview")
        print("="*60)

    print("="*60)
    print("办公智能体助手 已启动")
    print("="*60)
    print(f"访问地址: http://localhost:8000")
    print(f"API文档: http://localhost:8000/docs")
    print("="*60)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False
    )
