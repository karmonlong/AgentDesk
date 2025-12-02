"""
多智能体系统 - 支持 @ 交互的智能体团队
每个智能体都有独特的专长和个性
"""

from typing import Dict, List, Optional, Any, Callable
import urllib.request
import urllib.error
import requests
import base64
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


from services.mcp_service import mcp_manager

AGENT_IDS = {
    "文档分析师": "doc_analyst",
    "内容创作者": "content_creator",
    "数据专家": "data_expert",
    "校对编辑": "editor",
    "翻译专家": "translator",
    "合规官": "compliance_officer",
    "数据可视化专家": "dataviz",
    "知识管理专家": "knowledge_manager",
    "提示词智能体": "prompt_engineer",
    "协调者": "coordinator",
    "MCP助手": "mcp_assistant"
}

# Extend with specialized agents for market/operations
AGENT_IDS.update({
    "市场资讯捕手": "news_aggregator",
    "舆情分析师": "sentiment_analyst",
    "基金数据分析师": "fund_analyst",
    "投研报告助手": "report_assistant",
    "图像生成专家": "image_generator",
    "绘画智能体": "drawing_agent"
})

AGENT_ALIASES: Dict[str, List[str]] = {
    "数据可视化专家": ["绘图智能体", "绘画智能体"],
    "MCP助手": ["工具人", "连接器"]
}

def get_gemini_llm():
    """创建 Gemini LLM 实例"""
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-3-pro-preview")
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
        id: str,
        name: str,
        role: str,
        system_prompt: str,
        emoji: str = "fas fa-robot",
        temperature: float = 0.3
    ):
        self.id = id
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.emoji = emoji
        self.temperature = temperature
        self.color = "#FF6B00"
        self.desc = role
        self.capabilities: List[str] = []
        self.example = f"@{name} 你好"
        self.llm = None
        self._init_llm()
    
    def _init_llm(self):
        """初始化 LLM"""
        provider = os.getenv("LLM_PROVIDER", "gemini")
        api_key = os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY")
        model_name = os.getenv("LLM_MODEL_NAME") or os.getenv("GEMINI_MODEL", "gemini-3-pro-preview")
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
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-3-pro-preview",
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
        
        # 提取文本内容 - 处理可能的列表格式
        content = response.content
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and 'text' in item:
                    text_parts.append(item['text'])
                elif isinstance(item, str):
                    text_parts.append(item)
                else:
                    text_parts.append(str(item))
            return "\n".join(text_parts)
        elif isinstance(content, str):
            return content
        else:
            return str(content)
    
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
            id=AGENT_IDS["文档分析师"],
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
        self.color = "#795548"
        self.desc = "信息提取与分析专家"
        self.capabilities = ["关键信息提取", "结构化摘要", "实体识别", "主题分析"]
        self.example = "请从这份公告中提取关键数据并生成结构化摘要。"


class ContentCreatorAgent(Agent):
    """内容创作专家 - 擅长撰写报告、邮件、文章"""
    
    def __init__(self):
        super().__init__(
            id=AGENT_IDS["内容创作者"],
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
        self.color = "#9C27B0"
        self.desc = "专业内容撰写专家"
        self.capabilities = ["报告撰写", "邮件文案", "改写润色", "标题生成"]
        self.example = "请为年度总结撰写一封正式但不失亲和的邮件。"


class DataExpertAgent(Agent):
    """数据分析专家 - 擅长处理表格、数据分析、可视化建议"""
    
    def __init__(self):
        super().__init__(
            id=AGENT_IDS["数据专家"],
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
        self.color = "#00BCD4"
        self.desc = "数据分析与洞察专家"
        self.capabilities = ["表格分析", "趋势识别", "洞察生成", "可视化建议"]
        self.example = "请分析这份CSV中的销售数据并指出关键趋势。"


class EditorAgent(Agent):
    """校对编辑 - 擅长检查错误、优化表达、提升质量"""
    
    def __init__(self):
        super().__init__(
            id=AGENT_IDS["校对编辑"],
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
        self.color = "#4CAF50"
        self.desc = "内容质量把控专家"
        self.capabilities = ["语法检查", "表达优化", "逻辑连贯", "术语规范"]
        self.example = "请校对这篇文章并给出修改建议与改后稿。"


class ComplianceAgent(Agent):
    """合规官 - 负责审核内容合规性"""
    
    def __init__(self):
        super().__init__(
            id=AGENT_IDS["合规官"],
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
        self.color = "#F44336"
        self.desc = "合规与风险控制专家"
        self.capabilities = ["营销合规审查", "违规承诺识别", "风险揭示", "法规依据引用"]
        self.example = "请审查以下营销文案并给出合规修改建议。"


class TranslatorAgent(Agent):
    """翻译专家 - 擅长中英文翻译和本地化"""
    
    def __init__(self):
        super().__init__(
            id=AGENT_IDS["翻译专家"],
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
        self.color = "#3F51B5"
        self.desc = "专业翻译与本地化专家"
        self.capabilities = ["中英互译", "语气风格保持", "术语准确", "文化本地化"]
        self.example = "请将这段英文研报摘要翻译成专业但易读的中文。"


class DataVisualizationAgent(Agent):
    """数据可视化专家 - 生成HTML交互式图表"""
    
    def __init__(self):
        super().__init__(
            id=AGENT_IDS["数据可视化专家"],
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
        self.color = "#FF6B00"
        self.desc = "数据图表与可视化专家"
        self.capabilities = ["HTML图表", "Chart.js", "ECharts", "交互式仪表板"]
        self.example = "请用 Chart.js 画一个产品销售柱状图，配色现代。"


class ImageGeneratorAgent(Agent):
    def __init__(self):
        super().__init__(
            id=AGENT_IDS["图像生成专家"],
            name="图像生成专家",
            role="图像生成与编辑",
            emoji="fas fa-image",
            temperature=0.2,
            system_prompt="你负责根据自然语言生成图片，支持 Nano Banana 与 Nano Banana Pro 模型。"
        )
        self.color = "#FFC107"
        self.desc = "调用 Nano Banana/Nano Banana Pro 生成图片"
        self.capabilities = ["Nano Banana", "Nano Banana Pro", "文生图", "图片编辑"]
        self.example = "请用 Nano Banana Pro 生成一张科幻城市夜景海报，4K。"

    def _gen_via_api(self, prompt: str, model: str = "nano-banana-pro", size: str = "1024x1024") -> Dict[str, Any]:
        base = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")
        api_key = os.getenv("GEMINI_API_KEY")
        m = (model or "").strip().lower()
        if m.startswith("gemini-"):
            target = model
        elif m == "nano-banana-pro":
            target = "gemini-3-pro-image-preview"
        else:
            target = "gemini-2.5-flash-image"
        api_url = f"{base.rstrip('/')}/models/{target}:generateContent"
        
        print(f"\n[ImageGen] 配置信息:")
        print(f"  Base URL: {base}")
        print(f"  Target Model: {target}")
        print(f"  API URL: {api_url}")
        print(f"  API Key: {'已配置' if api_key else '未配置'}")
        
        if not api_key:
            return {
                "success": False,
                "error": "未配置 GEMINI_API_KEY",
                "hint": "请在 .env 文件中设置 GEMINI_API_KEY"
            }

        if "generativelanguage.googleapis.com" in api_url:
            aspect = "1:1"
            try:
                parts = size.lower().split("x")
                if len(parts) == 2:
                    w = int(parts[0])
                    h = int(parts[1])
                    if w == h:
                        aspect = "1:1"
                    elif w * 9 == h * 16:
                        aspect = "16:9"
                    elif w * 16 == h * 9:
                        aspect = "9:16"
                    elif w * 3 == h * 2:
                        aspect = "3:2"
                    elif w * 2 == h * 3:
                        aspect = "2:3"
                    elif w * 4 == h * 3:
                        aspect = "4:3"
                    elif w * 3 == h * 4:
                        aspect = "3:4"
                    elif w * 5 == h * 4:
                        aspect = "5:4"
                    elif w * 4 == h * 5:
                        aspect = "4:5"
                    elif w * 21 == h * 9:
                        aspect = "21:9"
            except Exception:
                aspect = "1:1"

            payload = {
                "contents": [
                    {"parts": [{"text": prompt}]}
                ]
            }
        else:
            payload = {
                "prompt": prompt,
                "model": model,
                "size": size
            }

        try:
            print(f"[ImageGen] 发送请求到 Gemini API...")
            resp = requests.post(
                api_url,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": api_key,
                },
                json=payload,
                timeout=120,
            )
            print(f"[ImageGen] 响应状态码: {resp.status_code}")
        except requests.Timeout:
            print(f"[ImageGen] 请求超时（120秒）")
            return {"success": False, "error": "请求超时", "hint": "Gemini 图像生成 API 响应超时（超过120秒），请稍后重试"}
        except Exception as e:
            print(f"[ImageGen] 请求异常: {e}")
            return {"success": False, "error": str(e), "hint": "网络连接失败或 API 不可用"}

        try:
            print(f"[ImageGen] POST {api_url} -> {resp.status_code}")
        except Exception:
            pass

        if resp.status_code != 200:
            body = resp.text[:500] if resp.text else ""
            print(f"[ImageGen] API 错误响应: {body}")
            hint = f"HTTP {resp.status_code}"
            # Fallback to local demo service if available
            try:
                demo_url = os.getenv("NANOBANANA_DEMO_URL", "http://localhost:3000/api/generate")
                print(f"[ImageGen] 尝试 fallback 到本地服务: {demo_url}")
                dr = requests.post(
                    demo_url,
                    headers={"Content-Type": "application/json"},
                    json={"prompt": prompt, "model": target},
                    timeout=120,
                )
                if dr.status_code == 200:
                    dj = dr.json()
                    b64 = dj.get("imageBase64")
                    if b64:
                        print(f"[ImageGen] ✓ 本地服务成功")
                        return {"success": True, "data": {"image_base64": b64}}
                    return {"success": True, "data": dj}
            except Exception as fallback_error:
                print(f"[ImageGen] 本地服务也失败: {fallback_error}")
                pass
            return {"success": False, "error": f"HTTP {resp.status_code}", "hint": f"API返回错误: {body[:100]}"}

        try:
            obj = resp.json()
            print(f"[ImageGen] 解析响应 JSON 成功")
        except Exception as e:
            print(f"[ImageGen] JSON 解析失败: {e}")
            obj = {"raw": base64.b64encode(resp.content).decode("utf-8")}

        if isinstance(obj, dict):
            try:
                cands = obj.get("candidates") or []
                print(f"[ImageGen] 找到 {len(cands)} 个候选结果")
                for c in cands:
                    content = c.get("content") or {}
                    parts_list = content.get("parts") or []
                    print(f"[ImageGen] 候选结果有 {len(parts_list)} 个 parts")
                    for idx, p in enumerate(parts_list):
                        print(f"[ImageGen] Part {idx}: keys={list(p.keys())}")
                        # 尝试两种命名方式：camelCase 和 snake_case
                        inline_camel = p.get("inlineData")
                        inline_snake = p.get("inline_data")
                        inline = inline_camel or inline_snake
                        
                        if inline and inline.get("data"):
                            print(f"[ImageGen] ✓ 成功提取图片数据（{'camelCase' if inline_camel else 'snake_case'}）")
                            return {"success": True, "data": {"image_base64": inline.get("data")}}
                print(f"[ImageGen] 未在响应中找到图片数据")
                print(f"[ImageGen] 完整响应: {str(obj)[:500]}...")
            except Exception as e:
                print(f"[ImageGen] 提取图片数据失败: {e}")
                import traceback
                traceback.print_exc()
                pass
        
        print(f"[ImageGen] 返回原始响应数据")
        return {"success": True, "data": obj}

    def invoke(self, messages: List[Any], context: Optional[Dict] = None) -> str:
        prompt = messages[-1].content if messages else ""
        model = "nano-banana-pro"
        size = "1024x1024"
        res = self._gen_via_api(prompt, model=model, size=size)
        if not res.get("success"):
            err = res.get("error", "生成失败")
            hint = res.get("hint")
            return f"生成图片失败: {err}{('，' + hint) if hint else ''}"
        data = res.get("data", {})
        if isinstance(data, dict) and data.get("image_base64"):
            b64 = data["image_base64"]
            return f"<img src=\"data:image/png;base64,{b64}\" style=\"max-width:100%\"/>"
        if isinstance(data, dict) and data.get("url"):
            return f"<img src=\"{data['url']}\" style=\"max-width:100%\"/>"
        return json.dumps(data, ensure_ascii=False)


class DrawingAgent(Agent):
    def __init__(self):
        super().__init__(
            id=AGENT_IDS["绘画智能体"],
            name="绘画智能体",
            role="绘画与多模态",
            emoji="fas fa-palette",
            temperature=0.3,
            system_prompt="根据自然语言选择或生成适合的图形表示，支持 Mermaid、PlantUML、Excalidraw 与 Nano Banana。只输出最终图形或图片。"
        )
        self.color = "#3F51B5"
        self.desc = "自然语言生成图形，支持 Mermaid、PlantUML、Excalidraw、Nano Banana"
        self.capabilities = ["Mermaid", "PlantUML", "Excalidraw", "Nano Banana", "下载导出"]
        self.example = "画一个团队组织架构图，包含研发、产品、运营"

    def invoke(self, messages: List[Any], context: Optional[Dict] = None) -> str:
        """重写 invoke 方法，支持通过聊天直接生成图片"""
        prompt = messages[-1].content if messages else ""
        
        # 检查用户是否指定了工具
        tools = None
        prompt_lower = prompt.lower()
        
        # 解析工具指定（例如："工具：Mermaid" 或 "工具：Nano Banana"）
        if "工具：" in prompt or "tool:" in prompt_lower or "tools:" in prompt_lower:
            import re
            tool_match = re.search(r'(?:工具|tool|tools)[：:]\s*([^\n]+)', prompt, re.IGNORECASE)
            if tool_match:
                tool_str = tool_match.group(1).strip()
                tools = [t.strip() for t in tool_str.split(',') if t.strip()]
        
        # 调用 generate_images 生成图片
        try:
            results = self.generate_images(prompt, tools)
            
            if not results:
                return "未能生成图片，请检查提示词或工具配置。"
            
            # 格式化返回结果
            output_parts = []
            for r in results:
                tool_name = r.get('tool', 'unknown')
                
                if r.get("image_base64"):
                    b64 = r["image_base64"]
                    mime = r.get("mime", "image/png")
                    output_parts.append(f"**{tool_name}** 生成成功：\n<img src=\"data:{mime};base64,{b64}\" style=\"max-width:100%; border-radius:8px; margin:10px 0;\"/>")
                    
                    # 如果有源代码，也显示
                    if r.get("source_code"):
                        source_code = r["source_code"]
                        output_parts.append(f"\n**源代码：**\n```\n{source_code[:500]}{'...' if len(source_code) > 500 else ''}\n```")
                elif r.get("error"):
                    err = r.get("error", "生成失败")
                    hint = r.get("hint", "")
                    output_parts.append(f"**{tool_name}** 生成失败：{err}{('，' + hint) if hint else ''}")
                else:
                    output_parts.append(f"**{tool_name}** 返回了数据，但未包含图片。")
            
            return "\n\n".join(output_parts)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"生成图片时出错：{str(e)}"

    def _llm_diagram(self, prompt: str, tool: str) -> str:
        p = (prompt or "").lower()
        t = tool.lower()
        kind = ""
        if t == "mermaid":
            if any(k in p for k in ["时序", "sequence", "登录", "调用链"]):
                kind = "sequenceDiagram"
                sys = f"""你是Mermaid图表专家。将用户需求转换为Mermaid时序图代码。

要求：
1. 仅输出Mermaid代码，不要任何解释文字
2. 第一行必须是 sequenceDiagram
3. 参与者使用中文或英文标签
4. 至少包含3个步骤，使用 ->> 表示消息
5. 代码要完整可运行

示例：
sequenceDiagram
    用户->>客户端: 发起请求
    客户端->>服务器: 验证身份
    服务器->>数据库: 查询数据
    数据库->>服务器: 返回结果
    服务器->>客户端: 响应数据
    客户端->>用户: 显示结果"""
            elif any(k in p for k in ["流程", "架构", "组织"]):
                kind = "graph TD"
                sys = f"""你是Mermaid图表专家。将用户需求转换为Mermaid流程图代码。

要求：
1. 仅输出Mermaid代码，不要任何解释文字
2. 第一行必须是 graph TD 或 graph LR
3. 节点使用中文或英文标签，用方括号包裹
4. 至少包含4个节点和3个连接
5. 使用 --> 表示连接关系
6. 代码要完整可运行

示例：
graph TD
    A[开始] --> B[需求分析]
    B --> C[系统设计]
    C --> D[开发实现]
    D --> E[测试验收]
    E --> F[上线部署]"""
            else:
                kind = "graph TD"
                sys = f"将输入转为Mermaid流程图代码，第一行必须是 graph TD，节点用方括号包裹，使用-->连接，至少4个节点。仅输出代码。"
        elif t == "plantuml":
            if any(k in p for k in ["时序", "sequence", "登录", "调用链"]):
                kind = "sequence"
                sys = """你是PlantUML专家。将用户需求转换为PlantUML时序图代码。

要求：
1. 仅输出PlantUML代码，不要任何解释文字
2. 第一行必须是 @startuml
3. 最后一行必须是 @enduml
4. 使用 participant 声明参与者
5. 使用 -> 或 --> 表示消息
6. 至少包含3个步骤
7. 代码要完整可运行

示例：
@startuml
participant 用户
participant 客户端
participant 服务器
participant 数据库

用户 -> 客户端: 发起请求
客户端 -> 服务器: 验证身份
服务器 -> 数据库: 查询数据
数据库 --> 服务器: 返回结果
服务器 --> 客户端: 响应数据
客户端 --> 用户: 显示结果
@enduml"""
            else:
                sys = """你是PlantUML专家。将用户需求转换为PlantUML组件图或用例图代码。

要求：
1. 仅输出PlantUML代码，不要任何解释文字
2. 第一行必须是 @startuml
3. 最后一行必须是 @enduml
4. 使用组件或用例元素
5. 使用 -> 或 --> 表示关系
6. 代码要完整可运行

示例：
@startuml
[研发部门] --> [产品部门]
[产品部门] --> [运营部门]
[运营部门] --> [市场部门]
@enduml"""
        elif t == "excalidraw":
            sys = """你是Excalidraw专家。将用户需求转换为Excalidraw JSON格式。

要求：
1. 仅输出有效的JSON字符串，不要任何解释文字
2. JSON必须包含 type, version, elements, appState, files 字段
3. elements数组至少包含3个元素（矩形、文本、箭头）
4. 每个元素必须有完整的坐标、尺寸、颜色等属性
5. 使用中文标签

示例JSON结构：
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [
    {
      "type": "rectangle",
      "id": "rect1",
      "x": 100,
      "y": 100,
      "width": 200,
      "height": 100,
      "strokeColor": "#1e1e1e",
      "backgroundColor": "#a5d8ff",
      "fillStyle": "solid"
    }
  ],
  "appState": {"viewBackgroundColor": "#ffffff"},
  "files": {}
}"""
        else:
            sys = f"将输入转为{tool}代码，仅输出代码。"
        msgs = [SystemMessage(content=sys), HumanMessage(content=prompt)]
        try:
            out = self.llm.invoke(msgs).content
            # 处理 LLM 返回 list 的情况
            if isinstance(out, list):
                out = "".join([str(item.get("text", "")) if isinstance(item, dict) else str(item) for item in out])
            return str(out).strip()
        except Exception as e:
            print(f"[DrawingAgent] LLM调用失败: {e}")
            return ""

    def _render_kroki(self, diagram_type: str, source: str) -> Dict[str, Any]:
        base = os.getenv("KROKI_BASE_URL", "https://kroki.io").rstrip("/")
        try:
            source = source.strip()
            source = re.sub(r"```\w*", "", source)
            source = re.sub(r"```", "", source)
        except Exception:
            pass
        if diagram_type == "excalidraw":
            url = f"{base}/excalidraw/svg"
            try:
                r = requests.post(url, json={"diagram_source": source}, headers={"Accept": "image/svg+xml"}, timeout=120)
            except Exception as e:
                return {"success": False, "error": str(e), "hint": "连接 Kroki 失败 (Excalidraw)"}
            if r.status_code != 200:
                return {"success": False, "error": f"HTTP {r.status_code}", "hint": r.text[:500]}
            b64 = base64.b64encode(r.content).decode("utf-8")
            return {"success": True, "image_base64": b64, "mime": "image/svg+xml"}
        else:
            url = f"{base}/{diagram_type}/svg"
            try:
                r = requests.post(url, headers={"Content-Type": "text/plain", "Accept": "image/svg+xml"}, data=source, timeout=120)
            except Exception as e:
                return {"success": False, "error": str(e), "hint": f"连接 Kroki 失败 ({diagram_type})"}
            if r.status_code != 200:
                # 尝试 fallback: 如果 mermaid 失败，尝试 plantuml
                if diagram_type == "mermaid" and "syntax error" in r.text.lower():
                     return {"success": False, "error": "Mermaid 语法错误", "hint": r.text[:500]}
                return {"success": False, "error": f"HTTP {r.status_code}", "hint": r.text[:500]}
            b64 = base64.b64encode(r.content).decode("utf-8")
            return {"success": True, "image_base64": b64, "mime": "image/svg+xml"}

    def _fallback_mermaid_to_plantuml(self, prompt: str) -> str:
        items = [w for w in ["研发", "产品", "运营"] if w in prompt]
        if not items:
            items = ["Dev", "Product", "Ops"]
        mapping = {"研发": "Dev", "产品": "Product", "运营": "Ops"}
        items = [mapping.get(x, x) for x in items]
        lines = ["@startuml"]
        for i in range(len(items)-1):
            lines.append(f"{items[i]} -> {items[i+1]}")
        lines.append("@enduml")
        return "\n".join(lines)

    def _normalize_source(self, tool: str, src: str, prompt: str) -> str:
        t = tool.lower()
        s = (src or "").strip()
        try:
            s = re.sub(r"```\w*", "", s)
            s = re.sub(r"```", "", s)
        except Exception:
            pass
        
        # 打印调试信息
        print(f"\n[DrawingAgent] 规范化 {t} 代码:")
        print(f"原始输出: {s[:200]}...")
        
        if t == "mermaid":
            has_type = any(x in s for x in ["graph ", "sequenceDiagram", "classDiagram", "stateDiagram", "erDiagram", "gantt", "pie "])
            if not has_type:
                print(f"[DrawingAgent] Mermaid缺少类型声明，使用fallback")
                pp = (prompt or "").lower()
                if any(k in pp for k in ["时序", "sequence", "登录", "调用链", "cas"]):
                    parts = [w for w in ["用户", "客户端", "CAS服务", "业务系统"] if any(k in prompt for k in [w, w.lower()])]
                    if not parts or len(parts) < 2:
                        parts = ["用户", "客户端", "CAS认证中心", "业务系统"]
                    lines = ["sequenceDiagram"]
                    for i in range(len(parts)-1):
                        lines.append(f"    {parts[i]}->>{parts[i+1]}: 步骤{i+1}")
                    s = "\n".join(lines)
                else:
                    items = [w for w in ["研发", "产品", "运营"] if w in prompt]
                    if not items or len(items) < 2:
                        items = ["需求分析", "系统设计", "开发实现", "测试部署"]
                    lines = ["graph TD"]
                    for i in range(len(items)):
                        node_id = chr(65 + i)  # A, B, C...
                        lines.append(f"    {node_id}[{items[i]}]")
                    for i in range(len(items)-1):
                        lines.append(f"    {chr(65+i)} --> {chr(65+i+1)}")
                    s = "\n".join(lines)
        elif t == "plantuml":
            if "@startuml" not in s:
                print(f"[DrawingAgent] PlantUML缺少@startuml/@enduml，使用fallback")
                pp = (prompt or "").lower()
                if any(k in pp for k in ["时序", "sequence", "登录", "调用链", "cas"]):
                    actors = [w for w in ["用户", "客户端", "CAS认证中心", "业务系统"] if any(k in prompt for k in [w, w.lower()])]
                    if not actors or len(actors) < 2:
                        actors = ["用户", "客户端", "CAS认证中心", "业务系统"]
                    lines = ["@startuml"]
                    for a in actors:
                        lines.append(f"participant {a}")
                    for i in range(len(actors)-1):
                        lines.append(f"{actors[i]} -> {actors[i+1]} : 认证流程{i+1}")
                    lines.append("@enduml")
                    s = "\n".join(lines)
                else:
                    items = [w for w in ["研发", "产品", "运营"] if w in prompt]
                    if not items or len(items) < 2:
                        items = ["研发部门", "产品部门", "运营部门", "市场部门"]
                    lines = ["@startuml"]
                    for i in range(len(items)):
                        lines.append(f"[{items[i]}]")
                    for i in range(len(items)-1):
                        lines.append(f"[{items[i]}] --> [{items[i+1]}]")
                    lines.append("@enduml")
                    s = "\n".join(lines)
        elif t == "excalidraw":
            try:
                parsed = json.loads(s)
                # 验证是否有有效的elements
                if not parsed.get("elements") or len(parsed.get("elements", [])) == 0:
                    raise ValueError("Empty elements")
            except Exception as e:
                print(f"[DrawingAgent] Excalidraw JSON解析失败或为空: {e}，使用fallback")
                # 根据 prompt 生成更丰富的 fallback
                pp = (prompt or "").lower()
                if any(k in pp for k in ["cas", "认证", "登录"]):
                    # 简化的 Excalidraw JSON，只包含必需字段
                    elements = [
                        {"type": "rectangle", "id": "r1", "x": 100, "y": 100, "width": 120, "height": 60, "strokeColor": "#000000", "backgroundColor": "#a5d8ff", "fillStyle": "solid", "strokeWidth": 2, "roughness": 0, "opacity": 100, "angle": 0, "seed": 1, "version": 1},
                        {"type": "text", "id": "t1", "x": 120, "y": 120, "width": 80, "height": 20, "text": "用户", "fontSize": 16, "fontFamily": 1, "textAlign": "center", "verticalAlign": "middle", "strokeColor": "#000000", "backgroundColor": "transparent", "fillStyle": "solid", "opacity": 100},
                        {"type": "arrow", "id": "a1", "x": 220, "y": 130, "width": 80, "height": 0, "strokeColor": "#000000", "backgroundColor": "transparent", "fillStyle": "solid", "strokeWidth": 2, "roughness": 0, "opacity": 100, "angle": 0, "seed": 2, "version": 1, "startBinding": None, "endBinding": None, "startArrowhead": None, "endArrowhead": "arrow", "points": [[0, 0], [80, 0]]},
                        {"type": "rectangle", "id": "r2", "x": 300, "y": 100, "width": 120, "height": 60, "strokeColor": "#000000", "backgroundColor": "#ffc9c9", "fillStyle": "solid", "strokeWidth": 2, "roughness": 0, "opacity": 100, "angle": 0, "seed": 3, "version": 1},
                        {"type": "text", "id": "t2", "x": 320, "y": 120, "width": 80, "height": 20, "text": "CAS", "fontSize": 16, "fontFamily": 1, "textAlign": "center", "verticalAlign": "middle", "strokeColor": "#000000", "backgroundColor": "transparent", "fillStyle": "solid", "opacity": 100}
                    ]
                    s = json.dumps({
                        "type": "excalidraw",
                        "version": 2,
                        "source": "https://excalidraw.com",
                        "elements": elements,
                        "appState": {"viewBackgroundColor": "#ffffff"},
                        "files": {}
                    })
                else:
                    # 通用场景
                    elements = [
                        {"type": "rectangle", "id": "r1", "x": 150, "y": 150, "width": 150, "height": 80, "strokeColor": "#000000", "backgroundColor": "#a5d8ff", "fillStyle": "solid", "strokeWidth": 2, "roughness": 0, "opacity": 100, "angle": 0, "seed": 1, "version": 1},
                        {"type": "text", "id": "t1", "x": 175, "y": 180, "width": 100, "height": 20, "text": "开始", "fontSize": 20, "fontFamily": 1, "textAlign": "center", "verticalAlign": "middle", "strokeColor": "#000000", "backgroundColor": "transparent", "fillStyle": "solid", "opacity": 100},
                        {"type": "arrow", "id": "a1", "x": 300, "y": 190, "width": 100, "height": 0, "strokeColor": "#000000", "backgroundColor": "transparent", "fillStyle": "solid", "strokeWidth": 2, "roughness": 0, "opacity": 100, "angle": 0, "seed": 2, "version": 1, "startBinding": None, "endBinding": None, "startArrowhead": None, "endArrowhead": "arrow", "points": [[0, 0], [100, 0]]},
                        {"type": "rectangle", "id": "r2", "x": 400, "y": 150, "width": 150, "height": 80, "strokeColor": "#000000", "backgroundColor": "#ffc9c9", "fillStyle": "solid", "strokeWidth": 2, "roughness": 0, "opacity": 100, "angle": 0, "seed": 3, "version": 1},
                        {"type": "text", "id": "t2", "x": 425, "y": 180, "width": 100, "height": 20, "text": "处理", "fontSize": 20, "fontFamily": 1, "textAlign": "center", "verticalAlign": "middle", "strokeColor": "#000000", "backgroundColor": "transparent", "fillStyle": "solid", "opacity": 100},
                        {"type": "arrow", "id": "a2", "x": 550, "y": 190, "width": 100, "height": 0, "strokeColor": "#000000", "backgroundColor": "transparent", "fillStyle": "solid", "strokeWidth": 2, "roughness": 0, "opacity": 100, "angle": 0, "seed": 4, "version": 1, "startBinding": None, "endBinding": None, "startArrowhead": None, "endArrowhead": "arrow", "points": [[0, 0], [100, 0]]},
                        {"type": "rectangle", "id": "r3", "x": 650, "y": 150, "width": 150, "height": 80, "strokeColor": "#000000", "backgroundColor": "#b2f2bb", "fillStyle": "solid", "strokeWidth": 2, "roughness": 0, "opacity": 100, "angle": 0, "seed": 5, "version": 1},
                        {"type": "text", "id": "t3", "x": 675, "y": 180, "width": 100, "height": 20, "text": "结束", "fontSize": 20, "fontFamily": 1, "textAlign": "center", "verticalAlign": "middle", "strokeColor": "#000000", "backgroundColor": "transparent", "fillStyle": "solid", "opacity": 100}
                    ]
                    s = json.dumps({
                        "type": "excalidraw",
                        "version": 2,
                        "source": "https://excalidraw.com",
                        "elements": elements,
                        "appState": {"viewBackgroundColor": "#ffffff"},
                        "files": {}
                    })
        
        print(f"[DrawingAgent] 规范化后: {s[:200]}...")
        return s

    def _choose_tools(self, prompt: str) -> List[str]:
        p = (prompt or "").lower()
        tools = []
        if any(k in p for k in ["海报", "照片", "壁纸", "写实", "照片风", "图像", "图片"]):
            tools.append("nano-banana")
        if any(k in p for k in ["流程", "流程图", "架构", "组织架构", "关系", "ER", "时序", "序列", "类图", "用例", "状态", "组件"]):
            tools.extend(["mermaid", "plantuml"])
        if any(k in p for k in ["手绘", "草图", "线稿", "涂鸦", "白板"]):
            tools.append("excalidraw")
        if not tools:
            tools = ["mermaid"]
        return list(dict.fromkeys(tools))

    def generate_images(self, prompt: str, tools: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        chosen = tools or self._choose_tools(prompt)
        results = []
        for t in chosen:
            tt = t.strip().lower()
            if tt in ["mermaid", "plantuml", "excalidraw"]:
                try:
                    print(f"\n[DrawingAgent] 正在使用LLM生成 {tt} 代码...")
                    src = self._llm_diagram(prompt, tt)
                    print(f"[DrawingAgent] LLM输出: {src[:100]}...")
                except Exception as e:
                    print(f"[DrawingAgent] LLM生成失败: {e}")
                    src = "" if tt in ["mermaid", "plantuml"] else json.dumps({"type":"excalidraw","elements":[]}, ensure_ascii=False)
                src = self._normalize_source(tt, src, prompt)
                print(f"[DrawingAgent] 最终代码: {src[:200]}...")
                rr = self._render_kroki(tt, src)
                if rr.get("success"):
                    print(f"[DrawingAgent] ✓ {tt} 渲染成功")
                    results.append({"tool": tt, "image_base64": rr.get("image_base64"), "mime": rr.get("mime", "image/png"), "source_code": src})
                else:
                    print(f"[DrawingAgent] ✗ {tt} 渲染失败: {rr.get('error')}")
                    if tt == "mermaid":
                        print(f"[DrawingAgent] 尝试Mermaid->PlantUML fallback")
                        puml = self._fallback_mermaid_to_plantuml(prompt)
                        rr2 = self._render_kroki("plantuml", puml)
                        if rr2.get("success"):
                            print(f"[DrawingAgent] ✓ PlantUML fallback成功")
                            results.append({"tool": "plantuml (fallback)", "image_base64": rr2.get("image_base64"), "mime": rr2.get("mime", "image/png"), "source_code": puml})
                        else:
                            results.append({"tool": tt, "error": rr.get("error"), "hint": rr.get("hint"), "source_code": src})
                    else:
                        results.append({"tool": tt, "error": rr.get("error"), "hint": rr.get("hint"), "source_code": src})
            elif tt in ["nano banana", "nano-banana", "nano-banana-pro", "gemini-3-pro-image-preview", "gemini-2.5-flash-image"]:
                model = "gemini-3-pro-image-preview" if tt in ["nano banana", "nano-banana", "nano-banana-pro"] else t
                ig = ImageGeneratorAgent()
                res = ig._gen_via_api(prompt, model=model, size="1024x1024")
                if res.get("success"):
                    d = res.get("data", {})
                    b64 = d.get("image_base64")
                    if b64:
                        results.append({"tool": "nano-banana", "image_base64": b64, "mime": "image/png"})
                    else:
                        results.append({"tool": "nano-banana", "data": d})
                else:
                    results.append({"tool": "nano-banana", "error": res.get("error"), "hint": res.get("hint")})
        return results
class NewsAggregatorAgent(Agent):
    """市场资讯捕手 - 聚合新闻与研报订阅"""
    def __init__(self):
        super().__init__(
            id=AGENT_IDS["市场资讯捕手"],
            name="市场资讯捕手",
            role="新闻研报聚合与订阅",
            emoji="fas fa-rss",
            temperature=0.3,
            system_prompt="""你是市场资讯捕手，负责聚合与订阅行业资讯与研报。

能力：
- 追踪指定主题的资讯（RSS/网站）
- 生成每日摘要与要点
- 提取关键信息与来源链接

输出：
- 列表化摘要，附带来源链接
- 可选生成 Markdown 日报
"""
        )
        self.color = "#FF5722"
        self.desc = "实时追踪 RSS 源与财经新闻"
        self.capabilities = ["新闻聚合", "关键词订阅", "自动摘要", "早报生成"]
        self.example = "帮我订阅‘半导体行业’相关的最新研报和新闻，每天早上8点推送摘要。"


class SentimentAnalystAgent(Agent):
    """舆情分析师 - 监控情绪与热点"""
    def __init__(self):
        super().__init__(
            id=AGENT_IDS["舆情分析师"],
            name="舆情分析师",
            role="社媒与股吧舆情分析",
            emoji="fas fa-poll",
            temperature=0.3,
            system_prompt="""你是舆情分析师，负责监控社交媒体与股吧，分析情绪与热点。

能力：
- 抓取与清洗讨论数据
- 进行情绪分析与热点提取
- 输出风险提示与趋势判断
"""
        )
        self.color = "#673AB7"
        self.desc = "监控社交媒体与股吧情绪"
        self.capabilities = ["情绪分析", "热点追踪", "风险预警", "竞品监控"]
        self.example = "分析最近一周关于‘宁德时代’的股吧讨论情绪，并生成风险提示报告。"


class FundAnalystAgent(Agent):
    """基金数据分析师 - 净值与持仓分析"""
    def __init__(self):
        super().__init__(
            id=AGENT_IDS["基金数据分析师"],
            name="基金数据分析师",
            role="基金净值与持仓分析",
            emoji="fas fa-chart-line",
            temperature=0.25,
            system_prompt="""你是基金数据分析师，擅长基金净值与持仓分析。

能力：
- 净值归因与同类排名
- 持仓穿透与行业分布分析
- 风险指标（波动率、回撤）
"""
        )
        self.color = "#00BCD4"
        self.desc = "基金净值与持仓分析"
        self.capabilities = ["净值归因", "持仓穿透", "业绩归因", "同类排名"]
        self.example = "对比‘招商中证白酒指数（161725）’与‘沪深300’近三年的收益率与最大回撤。"


class ResearchReportAssistantAgent(Agent):
    """投研报告助手 - 辅助撰写深度研报"""
    def __init__(self):
        super().__init__(
            id=AGENT_IDS["投研报告助手"],
            name="投研报告助手",
            role="深度投研报告辅助",
            emoji="fas fa-file-alt",
            temperature=0.6,
            system_prompt="""你是投研报告助手，辅助撰写深度投研报告。

能力：
- 生成研报结构与提纲
- 整理数据要点与图表位
- 逻辑校对与段落优化
"""
        )
        self.color = "#795548"
        self.desc = "辅助撰写深度投研报告"
        self.capabilities = ["研报框架", "数据填充", "逻辑校对", "图表插入"]
        self.example = "为‘人工智能行业2025展望’生成一个深度研报的大纲框架。"


class KnowledgeManagerAgent(Agent):
    """知识管理专家 - 基于向量检索的智能知识管理"""
    
    def __init__(self):
        super().__init__(
            id=AGENT_IDS["知识管理专家"],
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
        self.color = "#FF6B00"
        self.desc = "文档知识库与检索专家"
        self.capabilities = ["向量检索", "多文档对比", "智能问答", "精准引用"]
        self.example = "@知识管理专家 AgentDesk 有哪些核心功能和特色？"

    def invoke(self, messages: List[Any], context: Optional[Dict] = None) -> str:
        # 1. 获取用户查询
        query = messages[-1].content if messages else ""
        
        # 2. 执行向量检索
        # 延迟导入以避免循环依赖
        from tools.vector_store import vector_store_manager
        
        print(f"[KnowledgeManager] Searching for: {query}")
        search_results = vector_store_manager.search(query, k=5)
        
        # 3. 构建上下文
        if search_results:
            context_text = "\n\n".join([
                f"--- 来源: {r['metadata'].get('source', 'unknown')} (相似度: {r['similarity_score']:.2f}) ---\n{r['content']}"
                for r in search_results
            ])
            
            rag_prompt = f"""请基于以下从知识库中检索到的上下文信息回答用户的问题。
如果上下文信息不足以回答问题，请说明知识库中未找到相关信息。

用户问题: {query}

=== 检索到的上下文 ===
{context_text}
==================

请综合上述信息进行回答："""
            
            # 替换最后一条消息
            messages[-1] = HumanMessage(content=rag_prompt)
            print(f"[KnowledgeManager] RAG context injected ({len(search_results)} chunks)")
        else:
            print(f"[KnowledgeManager] No results found in knowledge base.")
            # 如果没有检索到结果，让 LLM 尝试直接回答或告知无数据
            pass
            
        # 4. 调用 LLM
        return super().invoke(messages, context)


class CoordinatorAgent(Agent):
    """协调者 - 负责任务分配和智能体协作"""
    
    def __init__(self):
        super().__init__(
            id=AGENT_IDS["协调者"],
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
        self.color = "#607D8B"
        self.desc = "任务分配与协调专家"
        self.capabilities = ["需求解析", "任务分配", "多智能体协作", "结果整合"]
        self.example = "请制定一个多智能体协作计划完成数据分析并撰写报告。"


class PromptAgent(Agent):
    def __init__(self):
        super().__init__(
            id=AGENT_IDS["提示词智能体"],
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
        self.color = "#9C27B0"
        self.desc = "提示词优化与设计"
        self.capabilities = ["提示词优化", "框架设计", "角色设定", "思维链拆解"]
        self.example = "优化这个提示词：‘帮我写个 Python 脚本’。"

class MCPAgent(Agent):
    """MCP 助手 - 能够连接外部工具的通用智能体"""
    
    def __init__(self):
        super().__init__(
            id=AGENT_IDS["MCP助手"],
            name="MCP助手",
            role="外部工具连接与执行者",
            emoji="fas fa-plug",
            temperature=0.0, # Use 0 for deterministic tool use
            system_prompt="""YOU ARE A TOOL-CALLING AGENT. Your ONLY job is to output JSON tool calls.

**CRITICAL RULES:**
1. NEVER analyze text
2. NEVER explain what you will do  
3. NEVER provide summaries
4. ONLY output JSON in code blocks

**Output Format:**
```json
{"tool": "tool_name", "args": {"arg": "value"}}
```

**Available Tools:**
- list_directory: list files, arg: path
- read_file: read file content, arg: path
- get_file_info: get file metadata, arg: path

**Examples:**

User: 列出当前目录
Assistant:
```json
{"tool": "list_directory", "args": {"path": "."}}
```

User: 读取README.md
Assistant:
```json
{"tool": "read_file", "args": {"path": "README.md"}}
```

User: uploads目录的文件
Assistant:
```json
{"tool": "list_directory", "args": {"path": "uploads"}}
```

**START NOW - OUTPUT ONLY JSON, NO OTHER TEXT.**"""
        )
        self.color = "#607D8B"
        self.desc = "连接外部数据与工具 (MCP)"
        self.capabilities = ["文件系统访问", "数据库查询", "API 集成", "本地命令执行"]
        self.example = "读取 /Documents 目录下的所有 PDF 文件。"

    async def invoke(self, messages: List[Any], context: Optional[Dict] = None) -> str:
        import re
        import json
        
        # 1. 获取当前 MCP 上下文
        command = os.environ.get("MCP_ACTIVE_COMMAND")
        args_str = os.environ.get("MCP_ACTIVE_ARGS", "[]")
        try:
            args = json.loads(args_str)
        except:
            args = []
            
        if not command:
            # 默认连接到本地文件系统
            command = "python"
            args = ["tools/mcp_server_fs.py"]
            os.environ["MCP_ACTIVE_COMMAND"] = command
            os.environ["MCP_ACTIVE_ARGS"] = json.dumps(args)

        # ReAct Loop
        max_steps = 5
        current_messages = messages.copy()
        
        # 注入工具描述
        tool_desc = """
[可用工具]
- list_directory(path): 列出目录
- read_file(path): 读取文件
- get_file_info(path): 文件信息
"""
        
        # 更新 System Prompt（添加工具描述和 few-shot 示例）
        enhanced_system_prompt = self.system_prompt + "\n" + tool_desc + """

**示例对话**:

用户: 列出当前目录
助手: ```json
{"tool": "list_directory", "args": {"path": "."}}
```

用户: 读取README.md
助手: ```json
{"tool": "read_file", "args": {"path": "README.md"}}
```

现在处理用户的实际请求："""
        
        # 替换第一个 SystemMessage
        if current_messages and isinstance(current_messages[0], SystemMessage):
            current_messages[0] = SystemMessage(content=enhanced_system_prompt)
        else:
            current_messages.insert(0, SystemMessage(content=enhanced_system_prompt))
            
        for _ in range(max_steps):
            # 1. Call LLM
            print(f"[MCPAgent] Step {_+1} invoking LLM...")
            try:
                response = self.llm.invoke(current_messages)
                content = response.content
                print(f"[MCPAgent] LLM Response (Raw): {str(content)[:200]}...")
            except Exception as e:
                print(f"[MCPAgent] LLM Invoke Error: {e}")
                return f"模型调用出错: {e}"
            
            # Handle empty content
            if not content:
                print("[MCPAgent] Empty response received.")
                return "我无法处理这个请求。请尝试更明确地描述您想要做什么。"

            # Convert list content to string if necessary
            if isinstance(content, list):
                # Check if list is empty
                if not content:
                    print("[MCPAgent] Empty list received.")
                    return "我无法处理这个请求。请尝试更明确地描述您想要做什么。"
                    
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and 'text' in item:
                        text_parts.append(item['text'])
                    elif isinstance(item, str):
                        text_parts.append(item)
                    else:
                        text_parts.append(str(item))
                content = "\n".join(text_parts)
                
                # Check if result is still empty after conversion
                if not content or not content.strip():
                    print("[MCPAgent] Empty content after list conversion.")
                    return "我无法处理这个请求。请尝试更明确地描述您想要做什么。"
            elif not isinstance(content, str):
                content = str(content)
            
            # 2. Check for tool call JSON
            # 宽松匹配
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
            if not json_match:
                json_match = re.search(r'(\{.*"tool".*"\})', content, re.DOTALL)
                
            if json_match:
                json_str = json_match.group(1)
                try:
                    tool_call = json.loads(json_str)
                    tool_name = tool_call.get("tool")
                    tool_args = tool_call.get("args", {})
                    
                    print(f"[MCPAgent] Calling tool: {tool_name} args={tool_args}")
                    
                    # 3. Execute Tool (直接 await 异步调用)
                    try:
                        result = await mcp_manager.call_tool(command, args, tool_name, tool_args)
                    except Exception as tool_error:
                        print(f"[MCPAgent] Tool call error: {tool_error}")
                        return f"❌ 工具调用失败: {str(tool_error)}"
                    
                    tool_output = str(result)
                    print(f"[MCPAgent] Tool Output len: {len(tool_output)}")
                    
                    # 尝试从 MCP 响应中提取实际内容
                    actual_content = tool_output
                    try:
                        # 检查是否是 MCP 响应对象
                        if "structuredContent" in tool_output and isinstance(result, dict):
                            actual_content = result.get("structuredContent", {}).get("result", tool_output)
                        elif hasattr(result, 'content') and result.content:
                            # 如果是 MCP 对象
                            if isinstance(result.content, list) and len(result.content) > 0:
                                actual_content = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
                        elif "'result':" in tool_output:
                            # 尝试提取 result 字段
                            import re
                            match = re.search(r"'result':\s*'([^']*)'", tool_output)
                            if match:
                                actual_content = match.group(1)
                    except Exception as e:
                        print(f"[MCPAgent] Failed to parse tool output: {e}")
                        pass
                    
                    # 对于单步查询操作，直接返回结果
                    if tool_name in ["list_directory", "get_file_info"] and _ == 0:
                        # 格式化输出
                        if tool_name == "list_directory":
                            try:
                                # 解析文件列表（可能是换行分隔的字符串）
                                if isinstance(actual_content, str):
                                    items = [f.strip() for f in actual_content.split('\n') if f.strip()]
                                else:
                                    items = [actual_content]
                                    
                                if len(items) > 0:
                                    formatted = f"📁 **目录清单** `{tool_args.get('path', '.')}`\n\n"
                                    for item in items[:30]:  # 最多显示30项
                                        # 判断文件类型
                                        icon = "📄"
                                        if '.' not in item or item.startswith('.'):
                                            icon = "📁"
                                        elif item.endswith(('.pdf', '.doc', '.docx', '.txt')):
                                            icon = "📄"
                                        elif item.endswith(('.jpg', '.png', '.gif', '.jpeg')):
                                            icon = "🖼️"
                                        elif item.endswith(('.zip', '.tar', '.gz')):
                                            icon = "📦"
                                        formatted += f"{icon} `{item}`\n"
                                    if len(items) > 30:
                                        formatted += f"\n_...以及其他 {len(items)-30} 项_"
                                    formatted += f"\n\n**总计**: {len(items)} 项"
                                    return formatted
                            except Exception as e:
                                print(f"[MCPAgent] Format error: {e}")
                                pass
                        
                        if tool_name == "get_file_info":
                            return f"📋 **文件信息**\n\n```\n{actual_content}\n```"
                        
                        return f"✅ 执行成功\n\n{actual_content}"
                    
                    # 对于 read_file，也直接返回
                    if tool_name == "read_file":
                        preview = actual_content[:1500] if len(actual_content) > 1500 else actual_content
                        return f"📄 **文件内容** `{tool_args.get('path', '?')}`\n\n```\n{preview}\n```\n\n{f'_内容较长，仅显示前1500字符，共 {len(actual_content)} 字符_' if len(actual_content) > 1500 else ''}"
                    
                    # 4. Add result to history (for multi-step operations)
                    current_messages.append(AIMessage(content=content))
                    current_messages.append(HumanMessage(content=f"Tool Result:\n{actual_content[:500]}\n\n{'...(truncated)' if len(actual_content) > 500 else ''}"))
                    
                except Exception as e:
                    print(f"[MCPAgent] Tool execution failed: {e}")
                    import traceback
                    traceback.print_exc()
                    return f"❌ 工具执行失败: {str(e)}"
            else:
                # No tool call, return final response
                return content
                
        return "任务执行步骤过多，已停止。"

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
            CoordinatorAgent(),
            NewsAggregatorAgent(),
            SentimentAnalystAgent(),
            FundAnalystAgent(),
            ResearchReportAssistantAgent(),
            ImageGeneratorAgent(),
            DrawingAgent(),
            MCPAgent()
        ]
        
        for agent in agents:
            self.register(agent)
    
    def register(self, agent: Agent):
        """注册智能体"""
        # 支持多种名称格式
        self.agents[agent.id] = agent
        self.agents[agent.name] = agent
        self.agents[f"@{agent.name}"] = agent
        
        # 为数据可视化专家添加别名
        for alias in AGENT_ALIASES.get(agent.name, []):
            self.agents[alias] = agent
            self.agents[f"@{alias}"] = agent
    
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
                "id": agent.id,
                "name": agent.name,
                "role": agent.role,
                "emoji": agent.emoji,
                "color": agent.color,
                "desc": agent.desc,
                "capabilities": agent.capabilities,
                "example": agent.example,
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
        """解析消息中的 @ 提及"""
        # 匹配 @ 后面的名称，遇到空白、标点符号就停止
        # 支持中文、英文、数字、下划线
        m = re.findall(r'@([\w\u4e00-\u9fa5]+)', text)
        # 只返回在注册表中能找到的智能体
        return [x for x in m if self.registry.get(x)]
    
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

        # 通用路由逻辑（先匹配专用类，再匹配通用类）
        if any(k in message_lower for k in ['新闻', '资讯', 'rss', '早报', '快讯', '订阅']):
            agent = self.registry.get("市场资讯捕手")
        elif any(k in message_lower for k in ['舆情', '情绪', '社交', '微博', '股吧', '热点']):
            agent = self.registry.get("舆情分析师")
        elif any(k in message_lower for k in ['基金', '净值', '持仓', '回撤', '收益率']):
            agent = self.registry.get("基金数据分析师")
        elif any(k in message_lower for k in ['投研', '研报', '大纲', '报告框架']):
            agent = self.registry.get("投研报告助手")
        elif any(k in message_lower for k in ['可视化', '图表', '画一个', '生成图', '柱状图', '饼图', '折线图', '仪表板', 'chart', 'html', 'uml', '时序图', '绘图', '画图']):
            agent = self.registry.get("数据可视化专家")
        elif any(k in message_lower for k in ['nano banana', 'nano banana pro', '生成图片', '海报', '插画', '壁纸', '图像生成']):
            agent = self.registry.get("图像生成专家")
        elif any(k in message_lower for k in ['合规', '审核', '风险', '违规', '法规', '监管']):
            agent = self.registry.get("合规官")
        elif any(k in message_lower for k in ['翻译', 'translate', '英文', '中文']):
            agent = self.registry.get("翻译专家")
        elif any(k in message_lower for k in ['数据', '表格', '统计', '趋势', '图表']):
            agent = self.registry.get("数据专家")
        elif any(k in message_lower for k in ['总结', '摘要', '提取', '分析文档', '关键信息']):
            agent = self.registry.get("文档分析师")
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
    
    async def chat(self, message: str, document: Optional[str] = None, scenario: Optional[str] = None) -> Dict[str, Any]:
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
        
        # 调用智能体（如果是异步的就 await）
        try:
            import inspect
            if inspect.iscoroutinefunction(agent.invoke):
                response = await agent.invoke(messages, self.conversation.get_context())
            else:
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
                            return await self._execute_plan(plan, document)
                    else:
                        # 尝试直接解析整个响应
                        try:
                            plan = json.loads(response)
                            if isinstance(plan, dict) and plan.get("type") == "plan":
                                return await self._execute_plan(plan, document)
                        except:
                            pass

                except Exception as e:
                    print(f"解析协调者计划失败: {e}")
                    pass

            return {
                "success": True,
                "agent": {
                    "id": agent.id,
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

    async def _execute_plan(self, plan: Dict, document: Optional[str] = None) -> Dict[str, Any]:
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
            
            # 执行步骤（如果是异步的就 await）
            import inspect
            if inspect.iscoroutinefunction(agent.invoke):
                response = await agent.invoke([HumanMessage(content=instruction)], step_context)
            else:
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
                "id": AGENT_IDS["协调者"],
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
