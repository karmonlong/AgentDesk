# LangGraph 办公智能体 Makefile
.PHONY: help install install-dev run dev test clean lint format check-env

# 默认目标
.DEFAULT_GOAL := help

# 配置变量
PYTHON := python3
VENV := venv
PIP := $(VENV)/bin/pip
PYTHON_VENV := $(VENV)/bin/python

# 从 .env 文件读取配置（如果存在）
ifneq (,$(wildcard .env))
    include .env
    export
endif

# 默认值
PORT ?= 8000
HOST ?= 0.0.0.0

# 帮助信息
help:
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════╗"
	@echo "║     LangGraph 办公智能体 - 快速启动菜单                     ║"
	@echo "╚══════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "📦 安装和配置:"
	@echo "  make install       - 安装项目依赖"
	@echo "  make install-dev   - 安装开发依赖（包括测试工具）"
	@echo "  make check-env     - 检查环境配置"
	@echo ""
	@echo "🚀 运行服务:"
	@echo "  make run           - 启动服务（生产模式）"
	@echo "  make dev           - 启动服务（开发模式，带热重载）"
	@echo ""
	@echo "🧪 测试和检查:"
	@echo "  make test          - 运行测试"
	@echo "  make lint          - 代码检查"
	@echo "  make format        - 代码格式化"
	@echo ""
	@echo "📊 管理:"
	@echo "  make clean         - 清理临时文件和缓存"
	@echo "  make clean-all     - 彻底清理（包括上传文件）"
	@echo "  make show-logs     - 查看日志"
	@echo ""
	@echo "📋 其他:"
	@echo "  make demo          - 运行演示示例"
	@echo "  make api-docs      - 打开 API 文档"
	@echo "  make status        - 检查服务状态"
	@echo ""

# 检查环境配置
check-env:
	@echo "🔍 检查环境配置..."
	@if [ ! -f .env ]; then \
		echo "⚠️  .env 文件不存在，正在从 .env.example 创建..."; \
		cp .env.example .env; \
		echo "❌ 请编辑 .env 文件并填写您的 GEMINI_API_KEY"; \
		exit 1; \
	fi
	@if grep -q "your-gemini-api-key-here" .env; then \
		echo "❌ 请将 .env 中的 GEMINI_API_KEY 替换为您的真实 API 密钥"; \
		exit 1; \
	fi
	@if ! grep -q "GEMINI_API_KEY=AIza" .env; then \
		echo "❌ GEMINI_API_KEY 未配置或格式不正确"; \
		exit 1; \
	fi
	@echo "✅ GEMINI_API_KEY 已配置"

# 安装依赖
install: check-env
	@echo "📦 安装项目依赖..."
	@if [ ! -d "$(VENV)" ]; then \
		echo "创建虚拟环境..."; \
		$(PYTHON) -m venv $(VENV); \
	fi
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "✅ 依赖安装完成！"

# 安装开发依赖
install-dev: install
	@echo "📦 安装开发依赖..."
	$(PIP) install pytest pytest-asyncio black flake8 isort pytest-cov
	@echo "✅ 开发依赖安装完成！"

# 启动服务（生产模式）
run: check-env
	@echo "🚀 启动服务（生产模式）..."
	@echo "访问地址: http://localhost:$(PORT)"
	@$(PYTHON_VENV) app.py

# 启动服务（开发模式，带热重载）
dev: check-env
	@echo "🚀 启动服务（开发模式）..."
	@echo "访问地址: http://localhost:$(PORT)"
	@echo "API文档: http://localhost:$(PORT)/docs"
	@$(PYTHON_VENV) -m uvicorn app:app --host $(HOST) --port $(PORT) --reload

# 运行测试
test:
	@echo "🧪 运行测试..."
	$(PYTHON_VENV) -m pytest tests/ -v

# 代码检查
lint:
	@echo "🔍 代码检查..."
	$(PYTHON_VENV) -m flake8 . --exclude venv,.venv,__pycache__,.trae --count --select=E9,F63,F7,F82 --show-source --statistics
	$(PYTHON_VENV) -m flake8 . --exclude venv,.venv,__pycache__,.trae --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# 代码格式化
format:
	@echo "✨ 代码格式化..."
	$(PYTHON_VENV) -m black . --line-length=100
	$(PYTHON_VENV) -m isort . --profile black

# 清理
clean:
	@echo "🧹 清理临时文件..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	@echo "✅ 临时文件已清理"

# 彻底清理（包括上传文件）
clean-all: clean
	@echo "🧹 彻底清理（包括上传文件和检查点）..."
	@if [ -d "uploads" ]; then \
		echo "清理 uploads 目录..."; \
		rm -rf uploads; \
		mkdir uploads; \
	fi
	@if [ -d "checkpoints" ]; then \
		echo "清理 checkpoints..."; \
		rm -rf checkpoints; \
	fi
	@echo "✅ 彻底清理完成"

# 查看日志
show-logs:
	@echo "📄 查看日志..."
	@if [ -f "logs/office-assistant.log" ]; then \
		tail -f logs/office-assistant.log; \
	else \
		echo "日志文件不存在"; \
	fi

# 运行演示
demo: check-env
	@echo "🎯 运行演示示例..."
	@echo "创建示例文档..."
	@mkdir -p uploads
	@echo "这是一份测试文档。\n\n这是第二段，包含一些数据：\n1. 2024年营收: $1,000,000\n2. 用户数: 10,000\n3. 增长率: 25%\n\n联系我们: test@example.com 或 电话: 138-0000-0000" > uploads/demo.txt
	@echo "运行处理..."
	@$(PYTHON_VENV) -c "from graph.document_graph import process_document; result = process_document('uploads/demo.txt', 'summarize'); print('\n=== 演示结果 ==='); print(result['result']); print('\n=== 完整结果已保存至 uploads 目录 ===')"

# 打开API文档
api-docs:
	@echo "📖 正在打开API文档..."
	@echo "请在浏览器中访问: http://localhost:$(PORT)/docs"
	@open http://localhost:$(PORT)/docs || echo "请手动打开: http://localhost:$(PORT)/docs"

# 检查服务状态
status:
	@echo "🔍 检查服务状态..."
	@curl -s http://localhost:$(PORT)/health | python3 -m json.tool || echo "服务未运行"

# 安装依赖（FastAPI版本）
install-fast:
	@echo "⚡ 快速安装（使用系统Python）..."
	pip install -r requirements.txt
	@echo "✅ 依赖安装完成！"
	@echo "提醒: 建议为生产环境使用虚拟环境"

# 快速启动（使用系统Python）
run-fast:
	@echo "⚡ 快速启动（使用系统Python）..."
	python app.py
