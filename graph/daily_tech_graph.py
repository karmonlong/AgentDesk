from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Optional, List, Dict, Any
from datetime import datetime
import re
from langchain_core.messages import HumanMessage
from agents.multi_agents import multi_agent_system


class DailyTechState(TypedDict):
    keywords: List[str]
    days: int
    need_en: bool
    raw_feed: Optional[str]
    clusters: Optional[str]
    summary: Optional[str]
    charts: Optional[str]
    report: Optional[str]
    translated: Optional[str]
    report_date: Optional[str]


def node_collect(state: DailyTechState) -> DailyTechState:
    data_agent = multi_agent_system.registry.get("数据专家")
    kw = ", ".join(state.get("keywords", []))
    days = state.get("days", 1)
    prompt = (
        f"基于关键词: {kw}，汇总最近{days}天的科技动态要点。"
        f"按主题列出来源、时间、摘要、影响，输出结构化要点列表。"
        f"如果无法联网，基于已知行业常识给出代表性动态示例。"
        f"在最后一行严格输出 'LATEST_DATE: YYYY-MM-DD'，为素材中最新日期，若不确定则为今天。"
    )
    resp = data_agent.invoke([HumanMessage(content=prompt)])
    state["raw_feed"] = resp
    m = re.search(r"LATEST_DATE:\s*(\d{4}-\d{2}-\d{2})", resp or "")
    if m:
        state["report_date"] = m.group(1)
    else:
        state["report_date"] = datetime.now().strftime("%Y-%m-%d")
    return state


def node_cluster(state: DailyTechState) -> DailyTechState:
    analyst = multi_agent_system.registry.get("文档分析师")
    feed = state.get("raw_feed", "")
    prompt = (
        "将以下素材去重并聚类为3-7个主题，给出每个主题的决策相关性评分(0-100)与代表事件。\n\n"
        + feed
    )
    resp = analyst.invoke([HumanMessage(content=prompt)])
    state["clusters"] = resp
    return state


def node_summarize(state: DailyTechState) -> DailyTechState:
    analyst = multi_agent_system.registry.get("文档分析师")
    clusters = state.get("clusters", "")
    prompt = (
        "根据主题聚类生成简明摘要，包含关键趋势、机会、风险与关注公司。"
        "输出分节小标题+要点。\n\n" + clusters
    )
    resp = analyst.invoke([HumanMessage(content=prompt)])
    state["summary"] = resp
    return state


def node_visualize(state: DailyTechState) -> DailyTechState:
    viz = multi_agent_system.registry.get("数据可视化专家")
    clusters = state.get("clusters", "")
    prompt = (
        "基于主题与评分，生成Mermaid饼图或柱状图，展示主题占比或重要度。"
        "只输出```mermaid```代码块，不要解释文字。\n\n" + clusters
    )
    resp = viz.invoke([HumanMessage(content=prompt)])
    state["charts"] = resp
    return state


def node_write(state: DailyTechState) -> DailyTechState:
    creator = multi_agent_system.registry.get("内容创作者")
    kw = ", ".join(state.get("keywords", []))
    summary = state.get("summary", "")
    charts = state.get("charts", "")
    today = state.get("report_date") or datetime.now().strftime("%Y-%m-%d")
    prompt = (
        f"撰写《每日科技动态》报告。关键词: {kw}。\n"
        f"日期：{today}\n"
        "结构：封面、目录、主题摘要、机会与风险、关注公司、可视化。\n"
        "语言：专业、简洁。报告头部日期必须与素材最新日期一致。\n"
        "包含以下Mermaid代码原样嵌入：\n\n"
        + summary
        + "\n\n"
        + charts
    )
    resp = creator.invoke([HumanMessage(content=prompt)])
    state["report"] = resp
    return state


def node_translate(state: DailyTechState) -> DailyTechState:
    if not state.get("need_en", False):
        return state
    translator = multi_agent_system.registry.get("翻译专家")
    report = state.get("report", "")
    prompt = "将以下日报翻译为英文，保留结构与Mermaid代码。\n\n" + report
    resp = translator.invoke([HumanMessage(content=prompt)])
    state["translated"] = resp
    return state


workflow = StateGraph(DailyTechState)
workflow.add_node("collect", node_collect)
workflow.add_node("cluster", node_cluster)
workflow.add_node("summarize", node_summarize)
workflow.add_node("visualize", node_visualize)
workflow.add_node("write", node_write)
workflow.add_node("translate", node_translate)
workflow.set_entry_point("collect")
workflow.add_edge("collect", "cluster")
workflow.add_edge("cluster", "summarize")
workflow.add_edge("summarize", "visualize")
workflow.add_edge("visualize", "write")
workflow.add_edge("write", "translate")
workflow.add_edge("translate", END)
memory = MemorySaver()
daily_tech_graph = workflow.compile(checkpointer=memory)


def run_daily_tech_flow(
    keywords: List[str],
    days: int = 1,
    need_en: bool = False,
) -> Dict[str, Any]:
    initial = DailyTechState(
        keywords=keywords,
        days=days,
        need_en=need_en,
        raw_feed=None,
        clusters=None,
        summary=None,
        charts=None,
        report=None,
        translated=None,
    )
    config = {"configurable": {"thread_id": "daily-tech"}}
    result = daily_tech_graph.invoke(initial, config=config)
    return result
