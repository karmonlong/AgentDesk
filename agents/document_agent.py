"""
文档处理智能体
基于 LangChain 的 ReAct 智能体，用于处理各类文档任务
配置为使用 Google Gemini
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Callable
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


# 创建 LLM 实例 - 使用 Google Gemini API
def get_gemini_llm():
    """创建 Gemini LLM 实例"""
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-3-pro-preview")
    temperature = float(os.getenv("GEMINI_TEMPERATURE", "0.3"))

    if not api_key:
        raise ValueError("❌ 未设置 GEMINI_API_KEY 环境变量，请在 .env 文件中配置")

    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
        google_api_key=api_key,
        convert_system_message_to_human=True
    )


llm = get_gemini_llm()


def create_document_agent():
    """
    创建一个文档处理智能体

    Returns:
        可执行的智能体链（直接调用 invoke 方法）
    """
    system_prompt = """你是一个专业的办公文档处理助手，擅长分析和处理各类文档。

你的核心能力：
1. 文档总结：提取关键信息，生成简洁准确的摘要
2. 内容生成：基于文档内容撰写报告、邮件、说明文档
3. 格式转换：将文档转换为结构化格式（如Markdown、JSON）
4. 信息提取：从文档中提取特定信息，如表格、数据、实体

工作原则：
- 始终基于提供的文档内容进行分析和处理
- 输出清晰、结构化、易于阅读的格式
- 遇到不清晰的指令或内容时，主动询问澄清
- 重要信息使用加粗、列表等方式突出显示
- 尽可能给出具体的、可操作的建议

输出格式要求：
- 使用 Markdown 格式
- 关键信息使用 **加粗**
- 使用列表和编号组织内容
- 长篇内容适当的分段和标题
- 必要时使用表格展示数据

如果你不确定如何处理，请标记为 ---CONFIDENCE_LOW--- 并在回复中说明原因。
"""

    prompt_template = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_prompt),
        MessagesPlaceholder(variable_name="messages")
    ])

    # 直接返回可执行的链（LangChain 1.0+ 支持 invoke 方法）
    agent = prompt_template | llm

    return agent


def create_structured_agent() -> Callable:
    """
    创建结构化输出的智能体（需要结构化结果时使用）

    Returns:
        可执行智能体的函数
    """
    system_prompt = """你是一个专业的文档分析助手。

你的任务是分析文档并提供结构化的输出。

请严格按照以下 JSON 格式回复：

```json
{
  "summary": "文档的简短摘要",
  "key_points": [
    "要点1",
    "要点2",
    "要点3"
  ],
  "entities": [
    {
      "type": "类型（如：人名、日期、金额）",
      "value": "实体值",
      "context": "上下文"
    }
  ],
  "action_items": [
    "待办事项1",
    "待办事项2"
  ],
  "questions": [
    "需要澄清的问题1",
    "需要澄清的问题2"
  ],
  "confidence": "high|medium|low",
  "notes": "额外备注"
}
```

要求：
1. 只输出 JSON，不输出任何其他内容
2. 如果没有某类信息，使用空数组 []
3. 置信度反映你对分析结果的确信程度
4. 尽可能提取完整信息
"""

    prompt_template = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_prompt),
        MessagesPlaceholder(variable_name="messages")
    ])

    agent = prompt_template | llm | StrOutputParser()

    return agent


def create_followup_questions_agent() -> Callable:
    """
    创建专门用于生成澄清问题的智能体

    Returns:
        可执行智能体的函数
    """
    system_prompt = """你是一个专业的需求分析师。

你的任务是分析用户请求，并生成需要澄清的关键问题。

请基于以下方面生成问题：
1. 目标和期望结果
2. 输出格式的具体要求
3. 受众和使用场景
4. 长度和详细程度
5. 其他特殊要求

问题应该：
- 具体且可回答
- 有助于提高输出的质量
- 避免显而易见的或不必要的问题
- 每类问题最多3个

输出格式：
- 使用 Markdown 列表形式
- 按类别分组（如：目标相关问题、格式相关问题）
"""

    prompt_template = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_prompt),
        HumanMessage(content="操作: {operation}\n文档片段: {content_snippet}\n请生成需要澄清的问题。")
    ])

    agent = prompt_template | llm | StrOutputParser()

    return agent


# 核心智能体实例
document_agent = create_document_agent()
structured_agent = create_structured_agent()
question_agent = create_followup_questions_agent()


# 方便的封装函数
def process_document_simple(content: str, operation: str, instruction: str = "") -> str:
    """
    简化版的文档处理函数

    Args:
        content: 文档内容
        operation: 操作类型
        instruction: 额外指示

    Returns:
        处理结果
    """
    prompt = f"""
操作类型: {operation}
{instruction if instruction else ''}

请处理以下内容:
{content}
"""

    messages = [
        HumanMessage(content=prompt)
    ]

    agent = create_document_agent()
    result = agent.invoke({"messages": messages})

    return result


__all__ = [
    "create_document_agent",
    "create_structured_agent",
    "create_followup_questions_agent",
    "document_agent",
    "structured_agent",
    "question_agent",
    "process_document_simple"
]
