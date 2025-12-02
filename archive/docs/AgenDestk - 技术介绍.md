# AgentDesk 系统技术介绍文档大纲

> 基于实际代码结构生成 | 版本：1.0 | 日期：2025-01-XX

---

## 📋 文档结构

### 第一部分：系统概览

#### 1.1 项目定位
- **一句话定位**：基于 LangGraph 1.0 的多智能体协作平台，专为资管行业打造
- **核心价值主张**：极简入口，极致专业，人机共生
- **目标用户**：投研人员、合规/风控人员、市场营销人员、运营/行政人员

#### 1.2 系统架构概览
- **技术栈**：
  - 后端框架：FastAPI 0.115+
  - AI 框架：LangGraph 1.0+ / LangChain 1.0+
  - LLM 引擎：Google Gemini 3 Pro / 支持 OpenAI/DeepSeek
  - 向量存储：ChromaDB + Google Gemini Embeddings
  - 前端技术：Bootstrap 5.3 + Font Awesome + Jinja2
  - 数据处理：Pandas, openpyxl, PyPDF2, python-docx

- **系统分层**：
  ```
  展示层 (Web UI)
    ├─ 传统界面 (/)
    ├─ 对话界面 (/chat)  
    └─ 指挥中心 (/command)
         ↓
  应用层 (FastAPI)
    ├─ 文档处理 API
    ├─ 多智能体对话 API
    ├─ 知识管理 API
    └─ 工作流 API
         ↓
  业务层 (LangGraph)
    ├─ 文档处理工作流 (document_graph)
    ├─ 合规审核工作流 (compliance_graph)
    └─ 日报生成工作流 (daily_tech_graph)
         ↓
  智能体层 (Multi-Agent System)
    ├─ AgentRegistry (注册中心)
    ├─ AgentRouter (智能路由)
    └─ 16个专业智能体
         ↓
  工具层 (Tools)
    ├─ 文件处理 (file_tools)
    ├─ 文档处理 (document_tools)
    └─ 向量存储 (vector_store)
  ```

---

### 第二部分：核心功能模块

#### 2.1 多智能体系统 (agents/multi_agents.py)

**智能体团队（16个专业AI）**

| 智能体名称 | ID | 角色 | 核心能力 | Temperature | 图标 |
|-----------|-----|------|---------|-------------|------|
| **文档分析师** | doc_analyst | 信息提取与分析专家 | 关键信息提取、结构化摘要、实体识别 | 0.2 | 📄 |
| **内容创作者** | content_creator | 专业内容撰写专家 | 报告/邮件/文案撰写、内容改写 | 0.7 | ✍️ |
| **数据专家** | data_expert | 数据分析与洞察专家 | 表格分析、趋势识别、可视化建议 | 0.3 | 📊 |
| **校对编辑** | editor | 内容质量把控专家 | 语法检查、表达优化、逻辑连贯 | 0.2 | ✅ |
| **翻译专家** | translator | 专业翻译与本地化 | 中英互译、术语准确、文化适配 | 0.4 | 🌐 |
| **合规官** | compliance_officer | 合规与风险控制 | 营销文案审核、违规识别、风险提示 | 0.1 | ⚖️ |
| **数据可视化专家** | dataviz | 数据图表与可视化 | 生成交互式HTML图表 (Chart.js/ECharts) | 0.3 | 📈 |
| **知识管理专家** | knowledge_manager | 文档知识库与检索 | 向量化存储、RAG检索、多文档分析 | 0.2 | 📖 |
| **提示词智能体** | prompt_engineer | 提示词优化与设计 | 优化AI提示词、结构化框架设计 | 0.3 | ✨ |
| **协调者** | coordinator | 任务分配与协调 | 任务分解、智能体选择、协作编排 | 0.1 | 🎯 |
| **市场资讯捕手** | news_aggregator | 新闻研报聚合 | RSS/新闻源追踪、每日摘要 | 0.2 | 📡 |
| **舆情分析师** | sentiment_analyst | 社媒与股吧舆情 | 情绪监控、热点追踪、风险预警 | 0.3 | 📊 |
| **基金数据分析师** | fund_analyst | 基金净值与持仓分析 | 净值归因、持仓穿透、排名对比 | 0.2 | 📉 |
| **投研报告助手** | report_assistant | 深度投研报告辅助 | 研报结构框架、数据要点整理 | 0.2 | 📝 |
| **图像生成专家** | image_generator | 图像生成与编辑 | 调用模型生成高质量图像、海报 | 0.7 | 🖼️ |
| **绘画智能体** | drawing_agent | 绘画与多模态 | 生成流程图(Mermaid)、架构图、手绘 | 0.5 | 🎨 |

**核心机制**：
- **@ 提及机制**：用户可通过 `@智能体名称` 精确指定智能体
- **智能路由**：系统自动解析用户意图，路由到最合适的智能体
- **对话管理**：ConversationManager 维护上下文和历史
- **多模型支持**：支持 Gemini、OpenAI、DeepSeek 等

#### 2.2 LangGraph 工作流系统 (graph/)

**2.2.1 文档处理工作流** (`document_graph.py`)
- **状态定义**：DocumentState (文件路径、内容、操作类型、结果等)
- **节点流程**：
  1. `node_read_file` - 读取文件
  2. `node_validate_file` - 验证文件
  3. `node_process_with_agent` - AI处理
  4. `node_check_review` - 审核检查
  5. `node_save_result` - 保存结果
- **支持操作**：summarize, generate, convert, extract_table, extract_key_points, analyze
- **状态持久化**：MemorySaver 支持检查点恢复

**2.2.2 合规审核工作流** (`compliance_graph.py`)
- **状态定义**：ComplianceState (主题、内容、审核结果、状态等)
- **循环流程**：
  1. `node_draft_content` - 内容创作者起草文案
  2. `node_compliance_review` - 合规官审核
  3. 条件判断：通过 → 结束，不通过 → 返回修改
- **最大迭代次数**：5次
- **应用场景**：营销文案合规审核闭环

**2.2.3 日报生成工作流** (`daily_tech_graph.py`)
- **功能**：基于关键词生成每日技术资讯报告
- **流程**：资讯收集 → 聚类分析 → 摘要生成 → 可视化 → 报告撰写
- **支持多语言**：中英文输出

#### 2.3 工具层 (tools/)

**2.3.1 文件处理工具** (`file_tools.py`)
- `detect_file_type()` - 文件类型检测
- `read_file()` - 多格式文件读取 (TXT, PDF, DOCX, XLSX, CSV, MD, JSON)
- `save_file()` - 文件保存
- `get_file_info()` - 文件信息获取

**2.3.2 文档处理工具** (`document_tools.py`)
- `get_operation_prompt()` - 根据操作类型生成提示词
- `create_summary_card()` - 创建摘要卡片
- `markdown_to_docx()` - Markdown 转 DOCX

**2.3.3 向量存储工具** (`vector_store.py`)
- **VectorStoreManager** 类：
  - `add_document()` - 添加文档到向量库
  - `search()` - 语义搜索
  - `list_documents()` - 列出所有文档
  - `delete_document()` - 删除文档
  - `get_document_by_id()` - 获取文档详情
- **技术实现**：ChromaDB + Google Gemini Embeddings
- **文本分割**：RecursiveCharacterTextSplitter (chunk_size=1000, overlap=200)

---

### 第三部分：用户界面

#### 3.1 传统界面 (`/`)
- **功能**：文档上传和处理
- **操作流程**：
  1. 选择文件上传
  2. 选择操作类型（总结/生成/转换/提取/分析）
  3. 填写额外指示（可选）
  4. 开始处理
  5. 下载结果
- **特点**：简单直接，适合快速批量处理

#### 3.2 对话界面 (`/chat`)
- **功能**：多智能体对话交互
- **核心特性**：
  - 支持文件上传
  - @ 提及智能体
  - 持续对话（上下文记忆）
  - 实时消息渲染
- **使用场景**：日常办公、复杂任务协作

#### 3.3 指挥中心 (`/command`)
- **功能**：可视化工作流监控和命令式交互
- **核心特性**：
  - 智能体节点可视化
  - 工作流动画展示
  - 实时日志输出
  - 状态监控面板
  - 快捷操作按钮
- **使用场景**：演示展示、工作流监控、高级用户

---

### 第四部分：API 接口

#### 4.1 文档处理 API
- `POST /upload` - 上传并处理文档
- `GET /download/{filename}` - 下载结果文件
- `GET /supported-formats` - 获取支持的文件格式
- `GET /recent-files` - 获取最近处理文件列表
- `GET /api/files` - 获取所有文件列表
- `POST /api/upload/simple` - 仅上传文件（不处理）
- `DELETE /api/files/{filename}` - 删除文件

#### 4.2 多智能体对话 API
- `POST /api/chat` - 与智能体对话
- `GET /api/agents` - 获取所有智能体列表
- `POST /api/chat/clear` - 清除对话历史
- `GET /api/chat/history` - 获取对话历史

#### 4.3 知识管理 API
- `POST /api/knowledge/add` - 添加文档到知识库
- `POST /api/knowledge/search` - 搜索知识库
- `GET /api/knowledge/list` - 列出知识库文档
- `DELETE /api/knowledge/{doc_id}` - 删除知识库文档
- `GET /api/knowledge/{doc_id}` - 获取文档详情

#### 4.4 工作流 API
- `POST /api/workflow/review` - 智能文档多维审查工作流
- `POST /api/workflow/daily_tech` - 每日技术资讯报告工作流
- `POST /api/compose/contest` - 参赛作品生成工作流

#### 4.5 图像生成 API
- `POST /api/image/generate` - 生成图像（Nano Banana等）
- `POST /api/draw/generate` - 生成流程图/架构图（Mermaid等）

#### 4.6 提示词优化 API
- `POST /api/prompt/optimize` - 优化提示词
- `GET /api/prompt/library` - 获取提示词库
- `POST /api/prompt/library` - 保存提示词
- `DELETE /api/prompt/library/{prompt_id}` - 删除提示词
- `GET /api/prompt/best-practices` - 获取最佳实践

#### 4.7 系统配置 API
- `GET /api/settings/model` - 获取模型配置
- `POST /api/settings/model` - 更新模型配置
- `GET /health` - 健康检查
- `GET /api/info` - API信息

---

### 第五部分：设计哲学与创新

#### 5.1 系统设计哲学（基于 `系统设计哲学.md`）
- **渐进式交互体验**：极简入口 → 专业工作台
- **拟人化协作范式**：智能体即同事，指挥官模式
- **场景化工作流**：封装完整业务场景

#### 5.2 核心创新点
- **"所想即所得"的智能路由架构**
- **多智能体协同引擎**（16个专业智能体）
- **"Chat + IDE"的融合界面形态**
- **深度垂直的行业能力组件**

#### 5.3 对基金公司的价值
- **提效降本**：重塑投研与运营流程
- **合规风控**：AI赋能的第一道防线
- **知识沉淀**：打造企业级"第二大脑"
- **数字化转型**：从"工具化"到"智能化"

---

### 第六部分：使用指南

#### 6.1 快速开始
- **环境要求**：Python 3.10+, Gemini API Key
- **安装步骤**：
  1. 克隆项目
  2. 配置环境变量（`.env`）
  3. 安装依赖（`make install`）
  4. 启动服务（`make run` 或 `make dev`）

#### 6.2 基础使用
- **文档处理**：上传 → 选择操作 → 获取结果
- **智能体对话**：使用 `@智能体名称` 或自动路由
- **知识管理**：添加文档 → 语义搜索 → 智能问答

#### 6.3 高级功能
- **工作流编排**：合规审核、日报生成
- **多智能体协作**：复杂任务自动分解
- **自定义提示词**：提示词优化和库管理

#### 6.4 最佳实践
- 如何选择合适的智能体
- 如何构建知识库
- 如何优化工作流

---

### 第七部分：技术架构详解

#### 7.1 代码结构
```
office-assistant/
├── app.py                      # FastAPI 主应用
├── agents/
│   ├── multi_agents.py        # 多智能体系统核心
│   ├── document_agent.py      # 文档处理智能体
│   └── prompt_manager.py       # 提示词管理器
├── graph/
│   ├── document_graph.py      # 文档处理工作流
│   ├── compliance_graph.py    # 合规审核工作流
│   └── daily_tech_graph.py    # 日报生成工作流
├── tools/
│   ├── file_tools.py           # 文件处理工具
│   ├── document_tools.py      # 文档处理工具
│   └── vector_store.py         # 向量存储工具
├── templates/
│   └── command_center_v2.html # 指挥中心界面
├── static/                     # 静态资源
├── uploads/                    # 上传文件存储
├── chroma_db/                  # 向量数据库
└── requirements.txt           # 依赖列表
```

#### 7.2 核心类设计
- **Agent**：智能体基类
- **AgentRegistry**：智能体注册中心
- **AgentRouter**：智能路由器
- **MultiAgentSystem**：多智能体系统主类
- **ConversationManager**：对话管理器
- **VectorStoreManager**：向量存储管理器

#### 7.3 数据流
- 用户输入 → 路由解析 → 智能体处理 → 结果返回
- 文档上传 → 工作流编排 → 多节点处理 → 结果保存

---

### 第八部分：部署与运维

#### 8.1 部署方式
- **开发模式**：`make dev` (热重载)
- **生产模式**：`make run` (直接运行)
- **Docker 部署**：（如有）

#### 8.2 配置说明
- **环境变量**：`.env` 文件配置
- **模型切换**：支持 Gemini/OpenAI/DeepSeek
- **存储配置**：上传目录、向量数据库路径

#### 8.3 监控与日志
- 日志系统
- 健康检查接口
- 错误处理机制

---

### 第九部分：扩展与定制

#### 9.1 添加新智能体
- 继承 `Agent` 基类
- 注册到 `AgentRegistry`
- 配置系统提示词和能力

#### 9.2 创建新工作流
- 定义状态类型（TypedDict）
- 实现节点函数
- 构建状态图（StateGraph）

#### 9.3 集成外部工具
- API 集成
- 数据库连接
- 第三方服务

---

### 第十部分：附录

#### 10.1 智能体完整列表
- 详细的能力说明
- 使用示例
- 最佳实践

#### 10.2 API 完整文档
- 所有接口的详细说明
- 请求/响应示例
- 错误码说明

#### 10.3 常见问题
- FAQ
- 故障排除
- 性能优化建议

#### 10.4 更新日志
- 版本历史
- 功能变更
- 已知问题

---

## 📝 文档编写建议

### 图文并茂的要求
1. **架构图**：系统分层架构、数据流图、工作流图
2. **界面截图**：三种界面的实际效果
3. **流程图**：智能体协作流程、工作流执行流程
4. **示例图**：使用场景示例、API调用示例
5. **对比表**：功能对比、性能对比

### 重点章节
- **第二部分**：核心功能模块（最重要，需要详细说明）
- **第三部分**：用户界面（需要大量截图）
- **第五部分**：设计哲学与创新（体现项目价值）
- **第六部分**：使用指南（用户最关心）

### 文档风格
- 专业但不失亲和
- 技术准确但易于理解
- 结构清晰，层次分明
- 图文并茂，视觉友好

---

**下一步行动**：
1. 收集界面截图和架构图
2. 完善每个章节的详细内容
3. 添加实际使用案例
4. 生成最终文档

