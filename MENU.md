# AgentDesk 办公智能体助手 - 系统菜单

本文档提供了 AgentDesk 办公智能体系统中当前可用页面、功能和智能体的全面概览。

## 🌐 网页界面

| 路径 | 描述 | 模板/视图 |
|------|-------------|---------------|
| `/` | **主页**: 系统主要入口，仪表盘概览。 | `command_center_v2.html` |
| `/command` | **指挥中心**: 与智能体交互和管理任务的主要界面。 | `command_center_v2.html` |
| `/chat` | **对话界面**: 重定向至指挥中心。 | *(重定向)* |
| `/analytics` | **分析仪表盘**: 重定向至指挥中心。 | *(重定向)* |
| `/docs` | **API 文档**: 后端 API 的自动生成 Swagger UI 文档。 | *(FastAPI 默认)* |

## 🚀 核心功能

### 1. 文档处理
上传文档（PDF, DOCX, TXT 等）进行自动化处理。
*   **总结文档 (Summarize)**: 提取核心信息并生成摘要。
*   **生成内容 (Generate Content)**: 基于上传的文档创作新内容。
*   **格式转换 (Convert Format)**: 在不同格式间转换文档（例如：Markdown 转 DOCX）。
*   **提取表格 (Extract Table)**: 解析并提取文档中的表格数据。
*   **提取要点 (Extract Key Points)**: 识别并列出关键信息点。
*   **深度分析 (Analyze)**: 对文档内容进行深度剖析。

### 2. 多智能体对话
通过指挥中心与专业 AI 智能体团队进行交互。
*   **智能路由**: 系统会自动将您的查询路由给最合适的智能体。
*   **@提及**: 使用 `@智能体名称` 指定呼叫某个智能体（例如：`@合规官`）。
*   **上下文感知**: 智能体可以读取上传的文档和历史对话内容。

### 3. 视觉与创意生成
*   **图像生成**: 使用 Nano Banana/Pro 等模型生成图像。
*   **图表绘制**: 生成流程图、时序图、甘特图等（支持 Mermaid, PlantUML, Excalidraw）。
*   **数据可视化**: 生成交互式 HTML 图表（柱状图、折线图、饼图等），使用 Chart.js 或 ECharts。

### 4. 知识库 (RAG)
*   **添加到知识库**: 将文档向量化并存储，用于长期记忆。
*   **搜索**: 对已存储的文档进行语义搜索。
*   **智能问答**: 智能体可以检索知识库中的信息来回答问题。

## 🔄 工作流

针对复杂任务的专用多步骤自动化流程。

| 工作流名称 | 描述 | 接口端点 |
|------------|-------------|----------|
| **合规审查 (Compliance Review)** | 分析文档风险并生成合规报告。（流程：分析师 -> 合规官 -> 创作者） | `/api/workflow/review` |
| **每日科技简报 (Daily Tech Report)** | 聚合指定关键词的新闻，聚类主题并生成报告。 | `/api/workflow/daily_tech` |
| **参赛方案生成 (Contest Entry)** | 分析项目文档并生成结构化的参赛作品/方案。 | `/api/compose/contest` |

## 🤖 可用智能体

系统由 `agents/multi_agents.py` 中定义的一组专业智能体驱动。

| 智能体名称 | 角色 | 核心能力 |
|------------|------|------------------|
| **协调者** (`Coordinator`) | 任务经理 | 任务拆解、智能体指派、结果整合。 |
| **文档分析师** (`Document Analyst`) | 分析师 | 信息提取、摘要生成、实体识别。 |
| **内容创作者** (`Content Creator`) | 作家 | 报告撰写、邮件起草、内容润色。 |
| **数据专家** (`Data Expert`) | 数据分析师 | 表格分析、趋势识别、洞察生成。 |
| **数据可视化专家** (`Data Visualization Expert`) | 可视化专家 | 生成 HTML/JS 图表 (Chart.js, ECharts)。 |
| **合规官** (`Compliance Officer`) | 风控专家 | 合规审查、风险识别、法规检查。 |
| **校对编辑** (`Editor`) | 质检员 | 语法检查、风格优化、逻辑审查。 |
| **翻译专家** (`Translator`) | 翻译 | 中英互译、本地化。 |
| **知识管理专家** (`Knowledge Manager`) | 图书管理员 | 知识库检索、跨文档分析。 |
| **提示词智能体** (`Prompt Engineer`) | 优化师 | 提示词优化、框架设计 (CRISPE/CO-STAR)。 |
| **图像生成专家** (`Image Generator`) | 艺术家 | 图像生成 (Nano Banana)。 |
| **绘画智能体** (`Drawing Agent`) | 绘图师 | 图表生成 (Mermaid, PlantUML, Excalidraw)。 |
| **市场资讯捕手** (`News Aggregator`) | 研究员 | 新闻追踪、RSS 聚合。 |
| **舆情分析师** (`Sentiment Analyst`) | 监控员 | 社交媒体/舆情分析。 |
| **基金数据分析师** (`Fund Analyst`) | 金融分析师 | 基金业绩与持仓分析。 |
| **投研报告助手** (`Report Assistant`) | 助手 | 研报大纲设计与起草辅助。 |

## 🔌 关键 API 接口

### 文件操作
*   `POST /upload`: 上传并处理文件。
*   `GET /download/{filename}`: 下载处理后的文件。
*   `GET /api/files`: 列出所有已上传的文件。
*   `DELETE /api/files/{filename}`: 删除文件。

### 对话与智能体
*   `POST /api/chat`: 发送消息给智能体系统。
*   `GET /api/agents`: 获取所有可用智能体列表。
*   `POST /api/chat/clear`: 清除对话历史。

### 知识库
*   `POST /api/knowledge/add`: 添加文档到向量库。
*   `POST /api/knowledge/search`: 搜索知识库。

### 专用功能
*   `POST /api/image/generate`: 生成图像。
*   `POST /api/draw/generate`: 生成绘图/图表。
*   `POST /api/prompt/optimize`: 优化提示词。
