"""
LangGraph 文档处理工作流
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Optional, Any, Dict
from tools.file_tools import read_file, detect_file_type, save_file
from tools.document_tools import get_operation_prompt
from agents.document_agent import create_document_agent
from langchain_core.messages import HumanMessage
import os
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class DocumentState(TypedDict):
    """文档处理状态"""
    file_path: str                  # 文件路径
    original_filename: str          # 原始文件名
    file_type: Optional[str]        # 文件类型
    content: Optional[str]          # 读取的文件内容
    operation: str                  # 操作类型: summarize | generate | convert | extract_table
    instruction: Optional[str]      # 用户的额外指令
    extracted_text: Optional[str]   # 提取的文本内容
    result: Optional[str]           # AI处理结果
    needs_review: bool              # 是否需要人工审核
    review_approved: Optional[bool]# 审核结果
    error: Optional[str]            # 错误信息
    metadata: Optional[Dict[str, Any]]  # 元数据


def node_read_file(state: DocumentState) -> DocumentState:
    """读取文件节点"""
    print(f"\n📄 正在读取文件: {state['original_filename']}")

    try:
        # 检测文件类型
        file_type = detect_file_type(state['file_path'])
        state['file_type'] = file_type
        print(f"   检测到的文件类型: {file_type}")

        # 读取文件内容
        content = read_file(state['file_path'], file_type)
        state['content'] = content
        state['extracted_text'] = content[:2000]  # 前2000字用于AI处理

        print(f"✅ 文件读取成功，共 {len(content)} 字符")

    except Exception as e:
        state['error'] = f"读取文件失败: {str(e)}"
        print(f"❌ {state['error']}")

    return state


def node_validate_file(state: DocumentState) -> DocumentState:
    """验证文件节点"""
    if state.get('error'):
        return state

    if not state.get('content'):
        state['error'] = "文件内容为空"

    return state


def node_process_with_agent(state: DocumentState) -> DocumentState:
    """调用AI智能体处理节点"""
    if state.get('error'):
        return state

    print(f"\n🤖 正在调用AI智能体进行: {state['operation']}")

    try:
        # 创建提示词
        prompt = get_operation_prompt(
            operation=state['operation'],
            content=state['extracted_text'][:4000],  # 限制token
            instruction=state.get('instruction', '')
        )

        print(f"   提示词预览: {prompt[:100]}...")

        # 调用智能体
        agent = create_document_agent()
        print(f"   DEBUG: Agent类型 = {type(agent)}")
        print(f"   DEBUG: Agent有invoke属性 = {hasattr(agent, 'invoke')}")

        # 调用智能体
        result = agent.invoke({"messages": [HumanMessage(content=prompt)]})

        print(f"   DEBUG: Result类型 = {type(result)}")
        print(f"   DEBUG: Result值 = {str(result)[:200]}...")

        # 提取AI响应内容
        ai_response = result.content if hasattr(result, 'content') else str(result)

        print(f"   DEBUG: ai_response类型 = {type(ai_response)}")
        print(f"   DEBUG: ai_response长度 = {len(ai_response) if ai_response else 0}")
        print(f"   DEBUG: ai_response前100字 = {str(ai_response)[:100]}...")

        # 设置结果
        state['result'] = ai_response

        print(f"✅ AI处理完成，结果长度: {len(ai_response) if ai_response else 0} 字符")

        # 判断是否需要审核（结果较长或需要人工确认的操作）
        needs_review_criteria = [
            len(ai_response) > 3000,  # 结果很长
            state['operation'] == 'generate',  # 生成内容
            '---CONFIDENCE_LOW---' in ai_response  # AI标记置信度低
        ]

        state['needs_review'] = any(needs_review_criteria)

        if state['needs_review']:
            print("   ⚠️  结果需要人工审核")

    except Exception as e:
        import traceback
        state['error'] = f"AI处理失败: {str(e)}"
        print(f"❌ {state['error']}")
        print(f"   错误详情: {traceback.format_exc()}")

    return state


def node_human_review(state: DocumentState) -> DocumentState:
    """人工审核节点 - 暂停等待人工决策"""
    if state.get('error'):
        return state

    print(f"\n👀 等待人工审核...")
    print(f"   操作: {state['operation']}")
    print(f"   文件名: {state['original_filename']}")
    print(f"   结果预览: {state['result'][:200]}...")

    # 在实际应用中，这里会暂停并等待外部审批
    # 审批通过后会设置 state['review_approved'] = True

    return state


def node_save_result(state: DocumentState) -> DocumentState:
    """保存结果节点"""
    if state.get('error'):
        return state

    try:
        # 生成输出文件名
        output_filename = f"{os.path.splitext(state['original_filename'])[0]}_{state['operation']}_result.txt"
        output_path = os.path.join('uploads', output_filename)

        # 保存处理结果
        save_file(output_path, state['result'])

        # 保存元数据
        metadata = {
            'original_file': state['original_filename'],
            'operation': state['operation'],
            'file_type': state['file_type'],
            'output_file': output_filename,
            'result_length': len(state['result']),
            'reviewed': state.get('review_approved', False)
        }

        metadata_path = output_path + '.metadata.json'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        state['metadata'] = metadata

        print(f"\n✅ 处理完成！")
        print(f"   结果已保存至: {output_path}")
        print(f"   元数据已保存至: {metadata_path}")

    except Exception as e:
        state['error'] = f"保存结果失败: {str(e)}"
        print(f"❌ {state['error']}")

    return state


def node_error_handler(state: DocumentState) -> DocumentState:
    """错误处理节点"""
    if state.get('error'):
        error_output = f"""
处理失败报告
================
错误: {state['error']}
文件名: {state['original_filename']}
操作: {state['operation']}

建议操作:
1. 检查文件是否存在且可读
2. 确认文件格式受支持
3. 检查 OpenAI API 密钥是否配置正确
4. 查看日志获取详细信息
        """

        error_path = os.path.join('uploads', f"{os.path.splitext(state['original_filename'])[0]}_error.txt")
        save_file(error_path, error_output)

        print(f"\n❌ 处理失败，错误报告已保存至: {error_path}")

    return state


# 定义条件函数
def should_review(state: DocumentState) -> str:
    """判断是否需要人工审核"""
    if state.get('error'):
        return "error_handler"
    if state['needs_review']:
        return "human_review"
    return "save_result"


def should_continue_after_review(state: DocumentState) -> str:
    """审核后判断是否继续"""
    if state.get('review_approved'):
        return "save_result"
    else:
        state['error'] = "人工审核未通过"
        return "error_handler"


# 创建工作流
workflow = StateGraph(DocumentState)

# 添加节点
workflow.add_node("read_file", node_read_file)
workflow.add_node("validate", node_validate_file)
workflow.add_node("process", node_process_with_agent)
workflow.add_node("human_review", node_human_review)
workflow.add_node("save_result", node_save_result)
workflow.add_node("error_handler", node_error_handler)

# 定义边
workflow.set_entry_point("read_file")
workflow.add_edge("read_file", "validate")
workflow.add_edge("validate", "process")

# 条件边: 根据是否需要审核进行分支
workflow.add_conditional_edges(
    "process",
    should_review,
    {
        "human_review": "human_review",
        "save_result": "save_result",
        "error_handler": "error_handler"
    }
)

# 人工审核后的条件边
workflow.add_conditional_edges(
    "human_review",
    should_continue_after_review,
    {
        "save_result": "save_result",
        "error_handler": "error_handler"
    }
)

# 错误处理 -> 结束
workflow.add_edge("error_handler", END)

# 保存结果 -> 结束
workflow.add_edge("save_result", END)

# 编译图（添加持久化）
memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)


def process_document(
    file_path: str,
    operation: str = "summarize",
    instruction: str = "",
    original_filename: str = None
) -> DocumentState:
    """
    处理文档的快捷函数

    Args:
        file_path: 文件路径
        operation: 操作类型: summarize/generate/convert/extract_table
        instruction: 用户的额外指示
        original_filename: 原始文件名

    Returns:
        处理后的状态
    """
    if original_filename is None:
        original_filename = os.path.basename(file_path)

    # 创建初始状态
    initial_state = DocumentState(
        file_path=file_path,
        original_filename=original_filename,
        operation=operation,
        instruction=instruction,
        file_type=None,
        content=None,
        extracted_text=None,
        result=None,
        needs_review=False,
        review_approved=None,
        error=None,
        metadata=None
    )

    print("=" * 60)
    print(f"开始处理文档: {original_filename}")
    print(f"操作类型: {operation}")
    print("=" * 60)

    # 执行工作流
    config = {"configurable": {"thread_id": "1"}}
    result = graph.invoke(initial_state, config=config)

    print("=" * 60)
    if result.get('error'):
        print(f"❌ 处理失败: {result['error']}")
    else:
        print("✅ 处理完成")
        if result.get('metadata'):
            output_file = result['metadata'].get('output_file')
            print(f"   结果文件: {output_file}")
    print("=" * 60)

    return result


# 导出主要函数供外部使用
__all__ = ["graph", "process_document", "DocumentState"]
