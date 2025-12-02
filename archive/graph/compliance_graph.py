"""
LangGraph 合规营销工作流
实现 内容创作者 <-> 合规官 的循环审批流
"""

from typing import TypedDict, Optional, List, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage
from agents.multi_agents import multi_agent_system

class ComplianceState(TypedDict):
    """合规营销状态"""
    topic: str                      # 营销主题
    content: Optional[str]          # 生成的文案
    review_result: Optional[str]    # 审核结果
    feedback: Optional[str]         # 修改建议
    status: str                     # current status: drafting | reviewing | approved | rejected
    iteration_count: int            # 迭代次数
    history: List[Dict]             # 对话历史

def node_draft_content(state: ComplianceState) -> ComplianceState:
    """起草/修改文案节点 (内容创作者)"""
    print(f"\n✍️ 正在起草/修改文案... (迭代: {state['iteration_count']})")
    
    creator = multi_agent_system.registry.get("内容创作者")
    
    if state['iteration_count'] == 0:
        prompt = f"请为主题 '{state['topic']}' 撰写一份吸引人的营销文案。"
    else:
        prompt = f"请根据合规官的以下反馈修改文案：\n\n{state['feedback']}\n\n原主题：{state['topic']}"
    
    response = creator.invoke([HumanMessage(content=prompt)])
    
    state['content'] = response
    state['status'] = 'reviewing'
    state['iteration_count'] += 1
    
    print(f"✅ 文案已生成 (长度: {len(response)})")
    return state

def node_compliance_review(state: ComplianceState) -> ComplianceState:
    """合规审核节点 (合规官)"""
    print(f"\n⚖️ 正在进行合规审核...")
    
    reviewer = multi_agent_system.registry.get("合规官")
    
    prompt = f"""请审核以下营销文案的合规性：

{state['content']}

请检查是否包含违规承诺（如保本、稳赚）、风险揭示是否充分。
如果通过，请回复"✅ 通过"。
如果不通过，请列出具体修改建议。"""

    response = reviewer.invoke([HumanMessage(content=prompt)])
    
    state['review_result'] = response
    
    if "✅ 通过" in response:
        state['status'] = 'approved'
        print("✅ 审核通过")
    else:
        state['status'] = 'drafting'
        state['feedback'] = response
        print("⚠️ 审核未通过，需要修改")
        
    return state

def should_continue(state: ComplianceState) -> str:
    """判断流程走向"""
    if state['status'] == 'approved':
        return "end"
    
    if state['iteration_count'] >= 3:
        print("⚠️ 达到最大迭代次数，强制结束")
        return "end"
        
    return "draft"

# 创建工作流
workflow = StateGraph(ComplianceState)

# 添加节点
workflow.add_node("draft", node_draft_content)
workflow.add_node("review", node_compliance_review)

# 定义边
workflow.set_entry_point("draft")
workflow.add_edge("draft", "review")

# 条件边
workflow.add_conditional_edges(
    "review",
    should_continue,
    {
        "draft": "draft",
        "end": END
    }
)

# 编译
memory = MemorySaver()
compliance_graph = workflow.compile(checkpointer=memory)

def run_compliance_flow(topic: str):
    """运行合规流程"""
    initial_state = ComplianceState(
        topic=topic,
        content=None,
        review_result=None,
        feedback=None,
        status="drafting",
        iteration_count=0,
        history=[]
    )
    
    config = {"configurable": {"thread_id": "1"}}
    result = compliance_graph.invoke(initial_state, config=config)
    return result
