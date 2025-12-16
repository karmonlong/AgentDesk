"""
AlphaFund 投研智能体 - 多智能体协同工作流
基于原生 Gemini API 实现（更稳定的网络层）
使用 Google Search 工具获取实时市场数据
"""

import os
import json
import asyncio
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# 初始化 Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def call_gemini_with_search(prompt: str, use_search: bool = False, temperature: float = 0.5) -> dict:
    """
    使用 REST API 调用 Gemini，支持 Google Search 工具
    返回 {"text": str, "sources": list}
    """
    if not GEMINI_API_KEY:
        return {"text": "⚠️ Gemini API 未配置", "sources": []}
    
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature
        }
    }
    
    # 启用 Google Search 工具
    if use_search:
        payload["tools"] = [{"googleSearch": {}}]
    
    try:
        resp = requests.post(
            api_url,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": GEMINI_API_KEY,
            },
            json=payload,
            timeout=120,
        )
        
        if resp.status_code != 200:
            return {"text": f"⚠️ API 错误: HTTP {resp.status_code} - {resp.text[:200]}", "sources": []}
        
        result = resp.json()
        text = ""
        sources = []
        
        # 提取文本内容
        candidates = result.get("candidates", [])
        if candidates:
            content = candidates[0].get("content", {})
            parts_list = content.get("parts", [])
            for part in parts_list:
                if "text" in part:
                    text += part["text"]
            
            # 提取搜索来源
            grounding_metadata = candidates[0].get("groundingMetadata", {})
            chunks = grounding_metadata.get("groundingChunks", [])
            for chunk in chunks:
                web = chunk.get("web", {})
                if web.get("uri") and web.get("title"):
                    sources.append({
                        "title": web["title"],
                        "url": web["uri"]
                    })
        
        # 去重来源
        unique_sources = list({s["url"]: s for s in sources}.values())
        
        return {"text": text, "sources": unique_sources}
        
    except Exception as e:
        return {"text": f"⚠️ 请求失败: {str(e)}", "sources": []}


class AlphaFundAgent:
    """AlphaFund 投研智能体系统"""
    
    AGENTS = [
        {"id": "deep", "name": "逻辑", "role": "DEEP_RESEARCHER", "color": "#fbbf24"},
        {"id": "alpha", "name": "天眼", "role": "MARKET_ANALYST", "color": "#f97316"},
        {"id": "sigma", "name": "西格玛", "role": "QUANT_ANALYST", "color": "#ea580c"},
        {"id": "prime", "name": "阿尔法", "role": "PORTFOLIO_MANAGER", "color": "#d4d4d4"},
        {"id": "critic", "name": "天平", "role": "CRITICAL_REVIEWER", "color": "#ef4444"},
        {"id": "canvas", "name": "幻境", "role": "VISUALIZATION_EXPERT", "color": "#14b8a6"},
        {"id": "shield", "name": "坚盾", "role": "RISK_OFFICER", "color": "#dc2626"},
    ]
    
    def __init__(self):
        self.shared_context: List[Dict] = []
    
    def format_context(self, history: List[Dict]) -> str:
        """格式化共享上下文"""
        if not history:
            return ""
        
        def extract_text(content):
            """从 content 中提取文本（兼容 str/list/dict）"""
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                parts = []
                for item in content:
                    if isinstance(item, dict) and 'text' in item:
                        parts.append(item['text'])
                    elif isinstance(item, str):
                        parts.append(item)
                    else:
                        parts.append(str(item))
                return "\n".join(parts)
            elif isinstance(content, dict) and 'text' in content:
                return content['text']
            else:
                return str(content)
        
        formatted = []
        for msg in history:
            formatted.append(f"--- [Agent: {msg.get('name', 'Unknown')} | Role: {msg.get('role', 'Unknown')}] ---")
            formatted.append(extract_text(msg.get('content', '')))
            formatted.append("---" * 20)
        return "\n".join(formatted)
    
    async def run_deep_researcher(self, topic: str) -> Dict:
        """深度研究智能体（逻辑）"""
        if not GEMINI_API_KEY:
            return {
                "role": "DEEP_RESEARCHER",
                "name": "逻辑",
                "content": "⚠️ Gemini API 未配置，无法执行深度研究。",
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
        
        prompt = f"""
你是一名代号为 '逻辑' 的首席战略官。
任务：对 "{topic}" 进行深度宏观逻辑推演。

请输出一份《深度战略研判简报》。

思考框架（必须使用中文作为章节标题）：
1. 【底层逻辑】该领域的价值创造机制是什么？
2. 【非共识洞察】识别市场普遍误判或忽视的结构性变化。
3. 【终局思维】基于技术与周期，推演未来 3-5 年的行业终局。

要求：
- **严禁使用英文标题**。所有 Markdown 标题（如 ###）必须是中文。
- 全程使用中文回答。
- 逻辑严密，避免陈词滥调。
"""
        
        try:
            result = call_gemini_with_search(prompt, use_search=False, temperature=0.7)
            
            return {
                "role": "DEEP_RESEARCHER",
                "name": "逻辑",
                "content": result["text"],
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
        except Exception as e:
            return {
                "role": "DEEP_RESEARCHER",
                "name": "逻辑",
                "content": f"⚠️ 深度研究模块故障: {str(e)}",
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
    
    async def run_market_analyst(self, topic: str, history: List[Dict]) -> Dict:
        """市场分析师智能体（天眼）- 使用 Google Search 获取实时市场情报"""
        if not GEMINI_API_KEY:
            return {
                "role": "MARKET_ANALYST",
                "name": "天眼",
                "content": "⚠️ Gemini API 未配置，无法执行市场分析。",
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
        
        context_str = self.format_context(history)
        
        prompt = f"""
你是一名代号为 '天眼' 的市场分析师。

=== 战略假设输入（共享上下文） ===
{context_str}
==================================

任务：基于上述战略假设，使用 Google Search 寻找实证数据。
目标板块：{topic}

请输出《市场情报综述》：
1. 宏观驱动力（引用政策或经济数据）。
2. 市场情绪量表（机构持仓态度与散户情绪）。
3. 近期催化剂（即将发生的重大事件）。

指令：
- **必须调用 Google Search 获取实时信源**。
- **Markdown 标题必须使用中文**（例如: ### 宏观驱动力）。
- 语言风格：专业、客观、数据驱动。
- **必须使用中文**撰写报告。
"""
        
        try:
            # 使用 Google Search 工具
            result = call_gemini_with_search(prompt, use_search=True, temperature=0.3)
            
            return {
                "role": "MARKET_ANALYST",
                "name": "天眼",
                "content": result["text"],
                "data": {"sources": result["sources"]},
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
        except Exception as e:
            return {
                "role": "MARKET_ANALYST",
                "name": "天眼",
                "content": f"⚠️ 市场分析师智能体故障: {str(e)}",
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
    
    async def run_quant_analyst(self, topic: str, history: List[Dict]) -> Dict:
        """量化分析师智能体（西格玛）- 使用 Google Search 获取实时股票数据"""
        if not GEMINI_API_KEY:
            return {
                "role": "QUANT_ANALYST",
                "name": "西格玛",
                "content": "⚠️ Gemini API 未配置，无法执行量化分析。",
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
        
        context_str = self.format_context(history)
        
        prompt = f"""
你是一名代号为 '西格玛' 的量化专家（必须中文输出）。

目标资产/板块：{topic}

=== 上下文回顾（共享上下文） ===
{context_str}
==================================

**核心任务**：
使用 Google Search 查找与 "{topic}" **相关的 5-8 个核心标的**的最新实时交易数据。

**重要**：不能只查询一个标的！必须查询多个相关公司/资产进行对比分析。

**搜索策略**：
- 如果是个股（如"招商银行"），搜索该公司及其竞争对手、供应链伙伴、同行业龙头
- 如果是板块（如"新能源"），搜索该板块内的多只龙头股
- 搜索关键词示例："{topic} competitors stock", "{topic} sector stocks", "{topic} industry comparison"

**输出格式（严格遵守）**：

**第一步：立即输出 Markdown 表格（必须包含 5-8 行数据）**

| 代码 | 名称 | 最新价 | PE TTM | 涨跌幅 | 市值 |
|---|---|---:|---:|---:|---:|
| XXX | 公司A | $xxx | xx.x | x.x% | xxxB |
| XXX | 公司B | $xxx | xx.x | x.x% | xxxB |
...（至少 5 行）

**市值格式要求**：使用数字+单位，如 "42700亿" 或 "4270B"（不要用 $4.27T 格式，用 4270B 或 42700亿）

**第二步：表格后给出 3-6 条中文要点结论**
- 使用 `- ` 项目符号
- 对比分析各标的的估值差异

**严格要求**：
1. 必须输出 5-8 个标的的数据（不能只有 1 个）
2. 严禁编造数据！必须从搜索结果中提取
3. 表格格式必须严格，前端会自动解析生成对比图表

现在立即开始，第一行就输出表格：
"""
        
        try:
            # 使用 Google Search 工具获取实时数据
            result = call_gemini_with_search(prompt, use_search=True, temperature=0.1)
            
            # Debug: 检查是否包含表格
            content = result["text"]
            has_table = '|' in content and '---' in content
            print(f"[AlphaFund] 量化分析输出长度: {len(content)}, 包含表格: {has_table}, 搜索来源数: {len(result['sources'])}")
            if not has_table:
                print(f"[AlphaFund] ⚠️ 量化分析缺少 Markdown 表格！")
            
            return {
                "role": "QUANT_ANALYST",
                "name": "西格玛",
                "content": content,
                "data": {"chartData": None, "sources": result["sources"]},
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
        except Exception as e:
            return {
                "role": "QUANT_ANALYST",
                "name": "西格玛",
                "content": f"⚠️ 量化分析师智能体故障: {str(e)}",
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
    
    async def run_portfolio_manager(self, topic: str, history: List[Dict]) -> Dict:
        """投资组合经理智能体（阿尔法）"""
        if not GEMINI_API_KEY:
            return {
                "title": f"{topic} 投资分析",
                "investmentThesis": "⚠️ Gemini API 未配置，无法生成投资备忘录。",
                "message": {
                    "role": "PORTFOLIO_MANAGER",
                    "name": "阿尔法",
                    "content": "⚠️ Gemini API 未配置",
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }
            }
        
        context_str = self.format_context(history)
        
        prompt = f"""
你是一名代号为 '阿尔法' 的基金经理。
目标资产：{topic}

=== 投委会会议记录（共享上下文） ===
{context_str}
====================================

任务：综合战略假设、市场情报、量化数据，撰写一份《投资决策备忘录》。

要求：
1. **必须使用中文**撰写，包括所有标题。
2. 论证严密：定性分析与定量支撑相结合。
3. 明确结论：给出具体的配置建议（超配/标配/低配）及操作思路。
4. 叙事生动：使用专业的金融叙事风格。

请以 JSON 格式输出：
{{
    "title": "专业且具有吸引力的研报标题（中文）",
    "investmentThesis": "详细的投资备忘录内容（中文）。Markdown 格式。"
}}
"""
        
        try:
            api_result = call_gemini_with_search(prompt, use_search=False, temperature=0.5)
            
            # 尝试解析 JSON
            text = api_result["text"].strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            try:
                result = json.loads(text)
            except:
                # 如果解析失败，使用原始文本
                result = {
                    "title": f"{topic} 投资分析报告",
                    "investmentThesis": text
                }
            
            return {
                "title": result.get("title", f"{topic} 投资分析"),
                "investmentThesis": result.get("investmentThesis", text),
                "message": {
                    "role": "PORTFOLIO_MANAGER",
                    "name": "阿尔法",
                    "content": f"标题: {result.get('title', '')}\n\n{result.get('investmentThesis', '')}",
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }
            }
        except Exception as e:
            return {
                "title": f"{topic} 投资分析",
                "investmentThesis": f"⚠️ 基金经理智能体故障: {str(e)}",
                "message": {
                    "role": "PORTFOLIO_MANAGER",
                    "name": "阿尔法",
                    "content": f"⚠️ 故障: {str(e)}",
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }
            }
    
    async def run_critic(self, history: List[Dict]) -> Dict:
        """独立评审专家智能体（天平）"""
        if not GEMINI_API_KEY:
            return {
                "role": "CRITICAL_REVIEWER",
                "name": "天平",
                "content": "⚠️ Gemini API 未配置，无法执行评审。",
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
        
        context_str = self.format_context(history)
        
        prompt = f"""
你是一名代号为 '天平' 的独立评审专家，负责【红队演练】。

=== 拟定投资策略全案（Trace） ===
{context_str}
==============================

任务：对上述投资决策进行【极限压力测试】。

请扮演"魔鬼代言人"，挑战团队的共识：
1. 识别盲点：指出被忽略的尾部风险（Tail Risk）或黑天鹅事件。
2. 逻辑归因：如果该策略失败，最可能的根本原因是什么？
3. 挑战假设：指出战略或分析可能存在的确认偏误。

输出一份简明扼要的《独立评审意见书》。
**要求：所有 Markdown 标题必须使用中文。**
"""
        
        try:
            result = call_gemini_with_search(prompt, use_search=False, temperature=0.7)
            
            return {
                "role": "CRITICAL_REVIEWER",
                "name": "天平",
                "content": result["text"],
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
        except Exception as e:
            return {
                "role": "CRITICAL_REVIEWER",
                "name": "天平",
                "content": f"⚠️ 评审专家智能体故障: {str(e)}",
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
    
    async def run_risk_officer(self, history: List[Dict]) -> Dict:
        """风险官智能体（坚盾）"""
        if not GEMINI_API_KEY:
            return {
                "score": 50,
                "critique": "⚠️ Gemini API 未配置，无法执行风险审查。",
                "approved": False
            }
        
        context_str = self.format_context(history)
        
        prompt = f"""
你是一名代号为 '坚盾' 的首席合规官（CRO）。

=== 决策链路审计（全链路追踪） ===
{context_str}
=====================================

任务：基于全链路信息，进行最终的【合规与风险审查】。

重点关注：
1. 策略是否符合常规的资产管理合规要求？
2. Reviewer 提出的尾部风险是否已得到充分重视？
3. 给出最终 "安全评分"（0-100）及一票否决权（通过/驳回）。

请以 JSON 格式输出：
{{
    "score": 0-100的整数,
    "critique": "风控合规意见（中文）",
    "approved": true/false
}}
"""
        
        try:
            api_result = call_gemini_with_search(prompt, use_search=False, temperature=0.1)
            
            # 尝试解析 JSON
            text = api_result["text"].strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            try:
                result = json.loads(text)
            except:
                result = {
                    "score": 60,
                    "critique": text if text else "风险审查完成，但无法解析详细结果。",
                    "approved": True
                }
            
            return result
        except Exception as e:
            return {
                "score": 0,
                "critique": f"⚠️ 风控智能体故障: {str(e)}",
                "approved": False
            }
    
    async def run_workflow_stream(self, topic: str, deep_research: bool = False):
        """执行完整的工作流（流式版本，逐个智能体yield）"""
        self.shared_context = []
        report_data = {
            "topic": topic,
            "status": "in_progress"
        }
        
        try:
            print(f"[AlphaFund] 开始流式工作流：{topic}，深度研究={deep_research}")
            
            # 1. 深度研究（可选）
            if deep_research:
                print("[AlphaFund] 执行：深度研究")
                deep_msg = await self.run_deep_researcher(topic)
                self.shared_context.append(deep_msg)
                report_data["deepResearchAnalysis"] = deep_msg.get("content", "")
                # 流式输出
                yield {"type": "agent_complete", "agent": deep_msg, "report": report_data.copy()}
            
            # 2. 市场分析
            print("[AlphaFund] 执行：市场分析")
            analyst_msg = await self.run_market_analyst(topic, self.shared_context)
            self.shared_context.append(analyst_msg)
            report_data["marketAnalysis"] = analyst_msg.get("content", "")
            report_data["sources"] = analyst_msg.get("data", {}).get("sources", [])
            yield {"type": "agent_complete", "agent": analyst_msg, "report": report_data.copy()}
            
            # 3. 量化分析
            print("[AlphaFund] 执行：量化分析")
            quant_msg = await self.run_quant_analyst(topic, self.shared_context)
            self.shared_context.append(quant_msg)
            report_data["quantAnalysis"] = quant_msg.get("content", "")
            report_data["chartData"] = quant_msg.get("data", {}).get("chartData")
            yield {"type": "agent_complete", "agent": quant_msg, "report": report_data.copy()}
            
            # 4. 投资组合经理
            print("[AlphaFund] 执行：投资组合经理")
            pm_result = await self.run_portfolio_manager(topic, self.shared_context)
            self.shared_context.append(pm_result["message"])
            report_data["title"] = pm_result.get("title", "")
            report_data["investmentThesis"] = pm_result.get("investmentThesis", "")
            yield {"type": "agent_complete", "agent": pm_result["message"], "report": report_data.copy()}
            
            # 5. 评审专家
            print("[AlphaFund] 执行：评审专家")
            critic_msg = await self.run_critic(self.shared_context)
            self.shared_context.append(critic_msg)
            report_data["critiqueAnalysis"] = critic_msg.get("content", "")
            yield {"type": "agent_complete", "agent": critic_msg, "report": report_data.copy()}
            
            # 6. 风险官
            print("[AlphaFund] 执行：风险官")
            risk_assessment = await self.run_risk_officer(self.shared_context)
            report_data["riskAssessment"] = risk_assessment
            
            report_data["status"] = "completed"
            report_data["agentContext"] = self.shared_context
            
            print(f"[AlphaFund] 工作流完成，agentContext 长度={len(self.shared_context)}")
            yield {"type": "complete", "report": report_data}
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            report_data["status"] = "error"
            report_data["error"] = str(e)
            report_data["agentContext"] = self.shared_context
            print(f"[AlphaFund] 工作流异常，已收集 agentContext={len(self.shared_context)} 条")
            yield {"type": "error", "error": str(e), "report": report_data}
    
    async def run_workflow(self, topic: str, deep_research: bool = False) -> Dict:
        """执行完整的工作流（非流式版本，保持向后兼容）"""
        report_data = None
        async for event in self.run_workflow_stream(topic, deep_research):
            if event["type"] in ["complete", "error"]:
                report_data = event["report"]
        return report_data if report_data else {"status": "error", "error": "No data returned"}
