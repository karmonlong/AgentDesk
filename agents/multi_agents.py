"""
多智能体系统 - 支持 @ 交互的智能体团队
每个智能体都有独特的专长和个性
"""

from typing import Dict, List, Optional, Any, Callable
from langchain_google_genai import ChatGoogleGenerativeAI
# Try to import ChatOpenAI, fallback if not found
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    try:
        from langchain_community.chat_models import ChatOpenAI
    except ImportError:
        ChatOpenAI = None

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
import os
import re
import json
from dotenv import load_dotenv

load_dotenv()


def get_gemini_llm():
    """创建 Gemini LLM 实例"""
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    temperature = float(os.getenv("GEMINI_TEMPERATURE", "0.3"))

    if not api_key:
        raise ValueError("❌ 未设置 GEMINI_API_KEY 环境变量")

    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
        google_api_key=api_key,
        convert_system_message_to_human=True
    )


class Agent:
    """智能体基类"""
    
    def __init__(
        self,
        name: str,
        role: str,
        system_prompt: str,
        emoji: str = "fas fa-robot",
        temperature: float = 0.3
    ):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.emoji = emoji
        self.temperature = temperature
        self.llm = None
        self._init_llm()
    
    def _init_llm(self):
        """初始化 LLM"""
        provider = os.getenv("LLM_PROVIDER", "gemini")
        api_key = os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY")
        model_name = os.getenv("LLM_MODEL_NAME") or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        base_url = os.getenv("LLM_BASE_URL")
        
        # Fallback for existing .env files or default to Gemini
        if not api_key and provider == "gemini":
             api_key = os.getenv("GEMINI_API_KEY")

        if provider == "gemini":
            if not api_key:
                # Default or error handling
                pass
            self.llm = ChatGoogleGenerativeAI(
                model=model_name,
                temperature=self.temperature,
                google_api_key=api_key,
                convert_system_message_to_human=True
            )
        elif provider in ["openai", "deepseek", "local"]:
            if ChatOpenAI is None:
                raise ImportError("langchain-openai or langchain-community not installed")
            
            self.llm = ChatOpenAI(
                model=model_name,
                temperature=self.temperature,
                api_key=api_key,
                base_url=base_url
            )
        else:
            # Default to Gemini if unknown
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                temperature=self.temperature,
                google_api_key=os.getenv("GEMINI_API_KEY"),
                convert_system_message_to_human=True
            )
    
    def invoke(self, messages: List[Any], context: Optional[Dict] = None) -> str:
        """调用智能体处理任务"""
        # 构建完整的消息列表
        full_messages = [SystemMessage(content=self.system_prompt)]
        full_messages.extend(messages)
        
        # 如果有上下文信息，添加到消息中
        if context:
            context_msg = self._format_context(context)
            if context_msg:
                full_messages.insert(1, HumanMessage(content=context_msg))
        
        # 调用 LLM
        response = self.llm.invoke(full_messages)
        return response.content
    
    def _format_context(self, context: Dict) -> Optional[str]:
        """格式化上下文信息"""
        parts = []
        
        if context.get('document'):
            parts.append(f"📄 **文档内容**:\n{context['document'][:1000]}...")
        
        if context.get('previous_results'):
            parts.append(f"📋 **之前的处理结果**:\n{context['previous_results']}")
        
        if context.get('user_feedback'):
            parts.append(f"💬 **用户反馈**:\n{context['user_feedback']}")
        
        return "\n\n".join(parts) if parts else None
    
    def __str__(self):
        return f"{self.emoji} **{self.name}** ({self.role})"


class DocumentAnalystAgent(Agent):
    """文档分析专家 - 擅长提取关键信息、总结要点"""
    
    def __init__(self):
        super().__init__(
            name="文档分析师",
            role="信息提取与分析专家",
            emoji="fas fa-file-alt",
            temperature=0.2,
            system_prompt="""你是一位专业的文档分析专家，名字叫"文档分析师"。

**核心能力**：
- 快速提取文档的核心信息和关键数据
- 生成结构化的文档摘要
- 识别文档中的重要实体（人名、日期、金额、地点等）
- 分析文档的主题和意图

**工作风格**：
- 精准：只提取确定的信息，不做推测
- 结构化：使用清晰的层级和列表
- 数据驱动：优先关注数字、日期、金额等硬数据

**输出格式**：
- 使用 Markdown 格式
- 关键信息用 **加粗** 标注
- 使用项目符号和编号列表
- 必要时使用表格展示数据

请始终保持专业、客观、高效的态度。"""
        )


class ContentCreatorAgent(Agent):
    """内容创作专家 - 擅长撰写报告、邮件、文章"""
    
    def __init__(self):
        super().__init__(
            name="内容创作者",
            role="专业内容撰写专家",
            emoji="fas fa-pen-fancy",
            temperature=0.7,
            system_prompt="""你是一位富有创意的内容创作专家，名字叫"内容创作者"。

**核心能力**：
- 撰写各类商务文档（报告、邮件、提案、总结）
- 内容改写和润色
- 根据目标受众调整语言风格
- 创意文案和标题生成

**工作风格**：
- 创意：善于用生动的语言表达
- 灵活：根据场景调整正式度和风格
- 用户导向：始终考虑目标受众的需求

**输出格式**：
- 清晰的段落结构
- 引人入胜的开头
- 逻辑清晰的论述
- 有力的总结

在创作时，我会考虑目标受众、使用场景和沟通目的，确保内容既专业又易读。"""
        )


class DataExpertAgent(Agent):
    """数据分析专家 - 擅长处理表格、数据分析、可视化建议"""
    
    def __init__(self):
        super().__init__(
            name="数据专家",
            role="数据分析与洞察专家",
            emoji="fas fa-chart-bar",
            temperature=0.3,
            system_prompt="""你是一位资深的数据分析专家，名字叫"数据专家"。

**核心能力**：
- 提取和分析表格数据
- 识别数据趋势和异常
- 生成数据洞察和建议
- 设计数据可视化方案

**工作风格**：
- 精确：对数字和计算一丝不苟
- 洞察：善于发现数据背后的故事
- 可视化：擅长用图表展示数据

**输出格式**：
- 使用表格展示数据
- 提供数据分析和解释
- 给出可视化建议
- 突出关键指标和趋势

我会用数据说话，提供有价值的商业洞察。"""
        )


class EditorAgent(Agent):
    """校对编辑 - 擅长检查错误、优化表达、提升质量"""
    
    def __init__(self):
        super().__init__(
            name="校对编辑",
            role="内容质量把控专家",
            emoji="fas fa-check-double",
            temperature=0.2,
            system_prompt="""你是一位严谨的校对编辑，名字叫"校对编辑"。

**核心能力**：
- 检查语法、拼写、标点错误
- 优化句式和表达
- 确保逻辑连贯性
- 提升内容可读性

**工作风格**：
- 严谨：不放过任何细节
- 建设性：不仅指出问题，还提供改进建议
- 标准化：确保术语和格式统一

**输出格式**：
- 列出发现的问题
- 提供修改建议
- 给出改进后的版本
- 解释修改原因

我的目标是让每一份文档都达到出版级别的质量。"""
        )


class ComplianceAgent(Agent):
    """合规官 - 负责审核内容合规性"""
    
    def __init__(self):
        super().__init__(
            name="合规官",
            role="合规与风险控制专家",
            emoji="fas fa-balance-scale",
            temperature=0.1,
            system_prompt="""你是一位严格的基金行业合规官，名字叫"合规官"。

**核心能力**：
- 审核营销文案是否符合《基金销售管理办法》
- 识别违规承诺（如"保本"、"稳赚"、"无风险"）
- 检查风险揭示是否充分
- 确保宣传内容真实、准确、完整

**工作风格**：
- 严格：对违规词汇零容忍
- 专业：引用相关法规条款作为依据
- 建设性：不仅指出问题，还提供合规的修改建议

**输出格式**：
- ✅ 通过：如果没有发现问题
- ⚠️ 风险提示：如果存在潜在风险
- ❌ 违规：如果存在明显违规
- 详细列出问题点和修改建议

请确保所有对外发布的材料都符合监管要求。"""
        )


class TranslatorAgent(Agent):
    """翻译专家 - 擅长中英文翻译和本地化"""
    
    def __init__(self):
        super().__init__(
            name="翻译专家",
            role="专业翻译与本地化专家",
            emoji="fas fa-language",
            temperature=0.4,
            system_prompt="""你是一位专业的翻译专家，名字叫"翻译专家"。

**核心能力**：
- 中英文双向翻译
- 保持原文的语气和风格
- 专业术语准确翻译
- 文化本地化处理

**工作风格**：
- 准确：忠于原文含义
- 流畅：目标语言自然地道
- 专业：正确处理行业术语

**输出格式**：
- 提供完整译文
- 标注重要术语的翻译选择
- 必要时提供多个翻译选项
- 说明翻译难点

我致力于让翻译既准确又自然，真正实现跨语言沟通。"""
        )


class DataVisualizationAgent(Agent):
    """数据可视化专家 - 生成HTML交互式图表"""
    
    def __init__(self):
        super().__init__(
            name="数据可视化专家",
            role="数据图表与可视化专家",
            emoji="fas fa-chart-line",
            temperature=0.4,
            system_prompt="""你是一位专业的数据可视化专家，名字叫"数据可视化专家"。

**核心能力**：
- 生成交互式 HTML 数据图表
- 使用 Chart.js、ECharts、D3.js 等库
- 创建响应式仪表板
- 数据动画和过渡效果
- 多图表组合展示

**工作风格**：
- 直观：选择最适合数据特征的图表类型
- 美观：使用专业的配色和设计
- 交互：添加悬停、缩放等交互功能
- 响应式：适配不同屏幕尺寸

**重要规则**：
1. **必须**将完整的HTML代码放在 ```html 代码块中
2. 代码必须是**独立可运行的**，包含所有必要的 CDN 引用
3. 使用轻量级库，优先选择：Chart.js（简单图表）、ECharts（复杂图表）、Mermaid（流程图）
4. 确保代码包含 <!DOCTYPE html>、<head>、<body> 等完整结构
5. 使用现代化的配色方案，优先使用橙色系（#FF6B00）作为主色
6. **推荐 CDN**：
   - ECharts: https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js
   - Chart.js: https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js
   - Mermaid: https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.9.0/mermaid.min.js

**输出格式示例**：

当用户请求"画一个销售数据的柱状图"时，你应该回复：

根据您的需求，我创建了一个交互式柱状图：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>销售数据柱状图</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>
</head>
<body style="margin: 0; padding: 20px; background: #0A0A0A; font-family: Arial, sans-serif;">
    <div style="max-width: 900px; margin: 0 auto;">
        <h2 style="color: #FF6B00; text-align: center;">2023年月度销售数据</h2>
        <canvas id="myChart"></canvas>
    </div>
    <script>
        const ctx = document.getElementById('myChart');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['1月', '2月', '3月', '4月', '5月', '6月'],
                datasets: [{
                    label: '销售额（万元）',
                    data: [12, 19, 15, 25, 22, 30],
                    backgroundColor: '#FF6B00',
                    borderColor: '#FF8800',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: true },
                    title: { display: false }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    </script>
</body>
</html>
```

**支持的图表类型**：
- 柱状图/条形图（bar/horizontalBar）
- 折线图（line）
- 饼图/环形图（pie/doughnut）
- 散点图（scatter）
- 面积图（area）
- 雷达图（radar）
- 仪表板（gauge）
- 热力图（heatmap）

记住：代码必须完整、可运行、美观！"""
        )


class KnowledgeManagerAgent(Agent):
    """知识管理专家 - 基于向量检索的智能知识管理"""
    
    def __init__(self):
        super().__init__(
            name="知识管理专家",
            role="文档知识库与检索专家",
            emoji="fas fa-book-open",
            temperature=0.3,
            system_prompt="""你是一位专业的知识管理专家，名字叫"知识管理专家"。

**核心能力**：
- 文档向量化存储和智能检索
- 多文档关联分析和对比
- 基于知识库的智能问答（RAG）
- 跨文档信息综合和提炼
- 知识关联和脉络梳理

**工作风格**：
- 系统化：构建结构化的知识体系
- 关联性：发现文档间的内在联系
- 可追溯：所有结论都有原文引用
- 精准：基于向量检索提供准确答案

**输出格式**：
- 使用 Markdown 格式
- 提供信息来源和引用
- 标注相关文档和章节
- 使用 **加粗** 强调关键信息
- 必要时提供多文档对比表格

**特殊能力**：
当用户询问知识库相关问题时，我会：
1. 理解用户的查询意图
2. 在向量数据库中检索相关内容
3. 综合多个相关片段
4. 提供准确且有引用的回答
5. 指出信息来源和可信度

我致力于将分散的文档转化为结构化的知识，让信息检索更高效、更智能。"""
        )


class CoordinatorAgent(Agent):
    """协调者 - 负责任务分配和智能体协作"""
    
    def __init__(self):
        super().__init__(
            name="协调者",
            role="任务分配与协调专家",
            emoji="fas fa-bullseye",
            temperature=0.1,
            system_prompt="""你是一位智能的任务协调者，名字叫"协调者"。

**核心能力**：
- 理解用户需求并分解任务
- 判断哪个智能体最适合处理任务
- 协调多个智能体协作完成复杂任务
- 整合多个智能体的输出

**工作风格**：
- 理解力强：快速把握用户真实需求
- 决策准确：选择最合适的智能体
- 协调有序：确保协作流畅高效

**智能体团队**：
- 文档分析师 (fas fa-file-alt) - 提取信息、分析文档
- 内容创作者 (fas fa-pen-fancy) - 撰写报告、邮件、文章
- 数据专家 (fas fa-chart-bar) - 分析数据、生成洞察
- 校对编辑 (fas fa-check-double) - 检查质量、优化表达
- 翻译专家 (fas fa-language) - 中英文翻译
- 合规官 (fas fa-balance-scale) - 审核合规性、风险控制
- 数据可视化专家 (fas fa-chart-line) - 生成HTML交互式图表和仪表板
- 知识管理专家 (fas fa-book-open) - 知识库检索、多文档分析

**输出格式**：
如果你认为任务需要多个智能体协作，或者需要分步骤完成，请**务必**输出以下 JSON 格式的执行计划（不要包含 markdown 代码块标记）：

{
    "type": "plan",
    "steps": [
        {
            "agent": "智能体名称",
            "instruction": "给该智能体的具体指令"
        },
        {
            "agent": "另一个智能体名称",
            "instruction": "给该智能体的指令"
        }
    ],
    "explanation": "简要说明为什么要这样安排"
}

如果任务很简单，只需要单个智能体回答，请直接返回你的回答或建议。
"""
        )


class PromptAgent(Agent):
    def __init__(self):
        super().__init__(
            name="提示词智能体",
            role="Prompt Engineer",
            system_prompt="""你是专业的提示词工程专家（Prompt Engineer）。
你的目标是帮助用户优化和设计高质量的 AI 提示词（Prompts）。

你的能力包括：
1. 优化提示词：分析用户提供的简单指令，将其转化为结构化、清晰且高效的提示词。
2. 结构化设计：使用 CRISPE、CO-STAR 等框架构建提示词。
3. 角色扮演：为提示词设定恰当的角色（Persona）和背景。
4. 任务拆解：将复杂任务拆解为思维链（Chain of Thought）。

请遵循以下原则：
- 始终以结构化的格式输出优化后的提示词。
- 解释你所做的修改和优化的理由。
- 针对不同的模型（如 GPT-4, Claude 3, Midjourney）提供特定的优化建议。
""",
            emoji="fas fa-magic",
            temperature=0.7
        )

class AgentRegistry:
    """智能体注册中心"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self._register_default_agents()
    
    def _register_default_agents(self):
        """注册默认智能体"""
        agents = [
            DocumentAnalystAgent(),
            ContentCreatorAgent(),
            DataExpertAgent(),
            EditorAgent(),
            TranslatorAgent(),
            ComplianceAgent(),
            DataVisualizationAgent(),
            KnowledgeManagerAgent(),
            PromptAgent(),
            CoordinatorAgent()
        ]
        
        for agent in agents:
            self.register(agent)
    
    def register(self, agent: Agent):
        """注册智能体"""
        # 支持多种名称格式
        self.agents[agent.name] = agent
        self.agents[agent.role] = agent
        self.agents[f"@{agent.name}"] = agent
        
        # 为数据可视化专家添加别名
        if agent.name == "数据可视化专家":
            self.agents["绘画智能体"] = agent
            self.agents["@绘画智能体"] = agent
    
    def get(self, name: str) -> Optional[Agent]:
        """获取智能体"""
        return self.agents.get(name) or self.agents.get(f"@{name}")
    
    def list_agents(self) -> List[Agent]:
        """列出所有智能体"""
        seen = set()
        unique_agents = []
        for agent in self.agents.values():
            if agent.name not in seen:
                seen.add(agent.name)
                unique_agents.append(agent)
        return unique_agents
    
    def get_agent_info(self) -> List[Dict]:
        """获取所有智能体信息"""
        return [
            {
                "name": agent.name,
                "role": agent.role,
                "emoji": agent.emoji,
                "mention": f"@{agent.name}"
            }
            for agent in self.list_agents()
        ]


class AgentRouter:
    """智能体路由器 - 自动选择合适的智能体"""
    
    def __init__(self, registry: AgentRegistry):
        self.registry = registry
        self.coordinator = registry.get("协调者")
    
    def parse_mentions(self, text: str) -> List[str]:
        """解析 @ 提及"""
        # 匹配 @智能体名称
        pattern = r'@(文档分析师|内容创作者|数据专家|校对编辑|翻译专家|合规官|数据可视化专家|知识管理专家|提示词智能体|协调者|绘画智能体)'
        mentions = re.findall(pattern, text)
        return mentions
    
    def route(self, message: str, context: Optional[Dict] = None, scenario: Optional[str] = None) -> Dict[str, Any]:
        """路由消息到合适的智能体"""
        # 检查是否有显式的 @ 提及
        mentions = self.parse_mentions(message)
        
        if mentions:
            # 用户显式指定了智能体
            agent_name = mentions[0]
            agent = self.registry.get(agent_name)
            
            # 移除消息中的 @ 提及 (更安全的方式)
            clean_message = message.replace(f"@{agent_name}", "", 1).strip()
            # 如果用户输入的是 @别名，也尝试移除
            if f"@{agent_name}" not in message and hasattr(agent, 'name'):
                 # 尝试移除标准名称
                 clean_message = message.replace(f"@{agent.name}", "", 1).strip()
            
            return {
                "agent": agent,
                "message": clean_message,
                "routing_type": "explicit",
                "all_mentions": mentions
            }
        
        # 否则，使用协调者自动判断
        return self._auto_route(message, context, scenario)
    
    def _auto_route(self, message: str, context: Optional[Dict] = None, scenario: Optional[str] = None) -> Dict[str, Any]:
        """自动路由（使用启发式规则 + LLM）"""
        # 简单的关键词匹配
        message_lower = message.lower()
        
        # 场景优先路由
        if scenario == 'compliance':
             # 合规场景下，优先使用合规官或内容创作者
            if any(k in message_lower for k in ['撰写', '生成', '文案']):
                agent = self.registry.get("内容创作者")
            else:
                agent = self.registry.get("合规官")
            
            return {
                "agent": agent,
                "message": message,
                "routing_type": "scenario_priority",
                "reason": f"基于合规场景优先选择了{agent.name}"
            }
            
        elif scenario == 'investment':
             # 投研场景下，优先使用文档分析师或数据专家
            if any(k in message_lower for k in ['数据', '表格', '趋势']):
                agent = self.registry.get("数据专家")
            else:
                agent = self.registry.get("文档分析师")
                
            return {
                "agent": agent,
                "message": message,
                "routing_type": "scenario_priority",
                "reason": f"基于投研场景优先选择了{agent.name}"
            }

        # 通用路由逻辑
        if any(k in message_lower for k in ['总结', '摘要', '提取', '分析文档', '关键信息']):
            agent = self.registry.get("文档分析师")
        elif any(k in message_lower for k in ['撰写', '写一份', '生成', '邮件', '报告', '文案']):
            agent = self.registry.get("内容创作者")
        elif any(k in message_lower for k in ['数据', '表格', '统计', '趋势', '图表']):
            agent = self.registry.get("数据专家")
        elif any(k in message_lower for k in ['检查', '校对', '修改', '优化', '润色']):
            agent = self.registry.get("校对编辑")
        elif any(k in message_lower for k in ['翻译', 'translate', '英文', '中文']):
            agent = self.registry.get("翻译专家")
        elif any(k in message_lower for k in ['合规', '审核', '风险', '违规', '法规', '监管']):
            agent = self.registry.get("合规官")
        elif any(k in message_lower for k in ['可视化', '图表', '画一个', '生成图', '柱状图', '饼图', '折线图', '仪表板', 'chart', 'html', 'uml', '时序图', '绘图', '画图']):
            agent = self.registry.get("数据可视化专家")
        elif any(k in message_lower for k in ['知识库', '检索', '搜索', '查找', '多文档', '对比', '关联', '知识']):
            agent = self.registry.get("知识管理专家")
        elif any(k in message_lower for k in ['协同', '合作', '配合', '团队', '流程', '先', '然后']):
            agent = self.registry.get("协调者")
        else:
            # 默认使用文档分析师
            agent = self.registry.get("文档分析师")
        
        return {
            "agent": agent,
            "message": message,
            "routing_type": "auto",
            "reason": f"根据关键词自动选择了{agent.name}"
        }


class ConversationManager:
    """对话管理器 - 管理多轮对话和上下文"""
    
    def __init__(self):
        self.history: List[Dict] = []
        self.context: Dict[str, Any] = {}
    
    def add_message(self, role: str, content: str, agent_name: Optional[str] = None):
        """添加消息到历史"""
        message = {
            "role": role,
            "content": content,
            "agent": agent_name,
            "timestamp": None  # 可以添加时间戳
        }
        self.history.append(message)
    
    def get_recent_messages(self, limit: int = 10) -> List[Dict]:
        """获取最近的消息"""
        return self.history[-limit:]
    
    def set_context(self, key: str, value: Any):
        """设置上下文信息"""
        self.context[key] = value
    
    def get_context(self, key: str = None) -> Any:
        """获取上下文信息"""
        if key:
            return self.context.get(key)
        return self.context
    
    def clear_history(self):
        """清除历史"""
        self.history = []
    
    def format_history_for_llm(self, limit: int = 5) -> List[Any]:
        """格式化历史消息供 LLM 使用"""
        recent = self.get_recent_messages(limit)
        formatted = []
        
        for msg in recent:
            if msg["role"] == "user":
                formatted.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                formatted.append(AIMessage(content=msg["content"]))
        
        return formatted


class MultiAgentSystem:
    """多智能体系统 - 统一的入口"""
    
    def __init__(self):
        self.registry = AgentRegistry()
        self.router = AgentRouter(self.registry)
        self.conversation = ConversationManager()
    
    def chat(self, message: str, document: Optional[str] = None, scenario: Optional[str] = None) -> Dict[str, Any]:
        """处理用户消息"""
        # 添加用户消息到历史
        self.conversation.add_message("user", message)
        
        # 如果有文档，添加到上下文
        if document:
            self.conversation.set_context("document", document)
        
        # 路由到合适的智能体
        routing_result = self.router.route(message, self.conversation.get_context(), scenario)
        agent = routing_result["agent"]
        clean_message = routing_result["message"]
        
        # 准备消息历史（包含最近的对话）
        history_messages = self.conversation.format_history_for_llm(limit=5)
        
        # 添加当前消息
        current_message = HumanMessage(content=clean_message)
        messages = history_messages + [current_message]
        
        # 调用智能体
        try:
            response = agent.invoke(messages, self.conversation.get_context())
            
            # 添加响应到历史
            self.conversation.add_message("assistant", response, agent.name)
            
            # 检查是否是协调者的计划
            if agent.name == "协调者":
                try:
                    # 尝试解析 JSON
                    # 使用正则提取 JSON 块
                    json_match = re.search(r'\{.*\}', response.replace('\n', ''), re.DOTALL)
                    if not json_match:
                         # 尝试查找 markdown 代码块中的 json
                        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
                    
                    if json_match:
                        json_str = json_match.group(1) if '```' in response else json_match.group(0)
                        plan = json.loads(json_str)
                        
                        if isinstance(plan, dict) and plan.get("type") == "plan":
                            # 执行计划
                            return self._execute_plan(plan, document)
                    else:
                        # 尝试直接解析整个响应
                        try:
                            plan = json.loads(response)
                            if isinstance(plan, dict) and plan.get("type") == "plan":
                                return self._execute_plan(plan, document)
                        except:
                            pass

                except Exception as e:
                    print(f"解析协调者计划失败: {e}")
                    pass

            return {
                "success": True,
                "agent": {
                    "name": agent.name,
                    "role": agent.role,
                    "emoji": agent.emoji
                },
                "response": response,
                "routing_info": {
                    "type": routing_result["routing_type"],
                    "reason": routing_result.get("reason", ""),
                    "mentions": routing_result.get("all_mentions", [])
                }
            }
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "agent": agent.name if agent else None
            }

    def _execute_plan(self, plan: Dict, document: Optional[str] = None) -> Dict[str, Any]:
        """执行多智能体计划"""
        steps = plan.get("steps", [])
        results = []
        current_context = document or ""
        
        execution_log = []
        
        for i, step in enumerate(steps):
            agent_name = step.get("agent")
            instruction = step.get("instruction")
            
            agent = self.registry.get(agent_name)
            if not agent:
                continue
                
            # 构建上下文：包含之前的执行结果
            step_context = {
                "document": document,
                "previous_results": "\n\n".join([f"--- {r['agent']} 的输出 ---\n{r['response']}" for r in results])
            }
            
            # 执行步骤
            response = agent.invoke([HumanMessage(content=instruction)], step_context)
            
            results.append({
                "agent": agent_name,
                "response": response
            })
            
            execution_log.append(f"### 步骤 {i+1}: {agent.name}\n**指令**: {instruction}\n\n{response}\n")
            
            # 将结果添加到对话历史
            self.conversation.add_message("assistant", response, agent.name)
            
        # 生成最终汇总
        final_response = f"**协同任务执行报告**\n\n{plan.get('explanation', '')}\n\n" + "\n".join(execution_log)
        
        return {
            "success": True,
            "agent": {
                "name": "协调者",
                "role": "任务分配与协调专家",
                "emoji": "fas fa-bullseye"
            },
            "response": final_response,
            "routing_info": {
                "type": "coordination",
                "reason": "执行了多智能体协同计划",
                "plan": plan
            }
        }
    
    def list_agents(self) -> List[Dict]:
        """列出所有可用的智能体"""
        return self.registry.get_agent_info()
    
    def get_conversation_history(self) -> List[Dict]:
        """获取对话历史"""
        return self.conversation.history
    
    def clear_conversation(self):
        """清除对话历史"""
        self.conversation.clear_history()
        self.conversation.context = {}

    def reload_agents(self):
        """重新加载所有智能体（用于更新配置后）"""
        print("🔄 正在重新加载智能体配置...")
        self.registry = AgentRegistry()
        self.router = AgentRouter(self.registry)
        print("✅ 智能体重新加载完成")


# 创建全局实例
multi_agent_system = MultiAgentSystem()


__all__ = [
    "Agent",
    "AgentRegistry",
    "AgentRouter",
    "ConversationManager",
    "MultiAgentSystem",
    "multi_agent_system"
]

