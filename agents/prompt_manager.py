import json
import os
import uuid
from typing import List, Dict, Optional
from agents.multi_agents import multi_agent_system, PromptAgent
from langchain_core.messages import HumanMessage

PROMPTS_FILE = "user_prompts.json"

# 丰富最佳实践内容
BEST_PRACTICES = [
    # Frameworks
    {
        "id": "bp_costar",
        "category": "框架 (Frameworks)",
        "title": "CO-STAR 框架",
        "content": """**CO-STAR 是一个结构化提示词的黄金框架，特别适合复杂任务。**

**C - Context (背景)**: 提供任务的背景信息。
**O - Objective (目标)**: 明确你想要实现什么。
**S - Style (风格)**: 指定写作风格（如专业、幽默、简洁）。
**T - Tone (语气)**: 设定情感基调（如正式、亲切、客观）。
**A - Audience (受众)**: 确定内容是给谁看的。
**R - Response (响应)**: 规定输出的格式（如 Markdown 列表、JSON、表格）。

---
📋 **资管行业示例：**

```
【背景】我是一家公募基金公司的产品经理，正在准备新发基金的路演材料。

【目标】撰写一份招商中证A500 ETF的产品介绍文案。

【风格】专业、数据驱动、突出亮点

【语气】自信但不过度营销，合规审慎

【受众】高净值个人投资者和机构客户

【响应格式】Markdown 格式，包含：
1. 产品概述（100字）
2. 投资策略（分点说明）
3. 核心亮点（3-5个）
4. 风险提示
```"""
    },
    {
        "id": "bp_crispe",
        "category": "框架 (Frameworks)",
        "title": "CRISPE 框架",
        "content": """**CRISPE 框架强调角色的设定和能力的定义，特别适合专业任务。**

**C - Capacity (能力)**: 设定 AI 的角色和专业能力。
**R - Role (角色)**: 进一步细化角色和视角。
**I - Insight (洞察)**: 提供必要的背景信息和上下文。
**S - Statement (陈述)**: 明确具体的任务指令。
**P - Personality (个性)**: 设定回复的风格。
**E - Experiment (尝试)**: 要求 AI 提供多个选项供选择（可选）。

---
📋 **资管行业示例：**

```
【能力】你是一位拥有15年经验的资深基金经理

【角色】作为 A 股市场的价值投资者

【洞察】
- 当前市场处于震荡期
- 沪深300PE为12倍，处于历史低位
- 央行近期有降准预期

【任务】分析招商中证A500 ETF的当前投资价值

【个性】
- 客观理性，数据说话
- 适度审慎，不过度乐观

【尝试】请从3个不同角度分析：
1. 估值角度
2. 行业配置角度
3. 资金流向角度
```"""
    },
    {
        "id": "bp_broke",
        "category": "框架 (Frameworks)",
        "title": "BROKE 框架",
        "content": """**BROKE 框架适用于需要迭代优化的任务，定义清晰的成功标准。**

**B - Background (背景)**: 陈述背景。
**R - Role (角色)**: 设定角色。
**O - Objective (目标)**: 设定目标。
**K - Key Result (关键结果)**: 定义成功的标准。
**E - Evolve (进化)**: 根据反馈进行调整。

---
📋 **资管行业示例：**

```
【背景】公司计划推出一款面向年轻投资者的定投产品

【角色】你是产品设计专家

【目标】设计产品营销方案

【关键结果】
✅ 方案需覆盖线上线下渠道
✅ 突出"轻松理财"概念
✅ 符合合规要求，无夸大宣传
✅ 包含用户触达策略

【迭代】基于我的反馈持续优化方案
```"""
    },
    
    # Techniques
    {
        "id": "bp_cot",
        "category": "技巧 (Techniques)",
        "title": "思维链 (Chain of Thought)",
        "content": """**通过引导模型展示推理过程，显著提高复杂逻辑推理和决策任务的准确率。**

**方法 1 (Zero-Shot)**: 在提示词末尾加上 *"让我们一步步思考"*。
**方法 2 (Few-Shot)**: 提供展示推理步骤的示例。

---
📋 **资管行业示例：**

```
请分析招商中证A500 ETF的投资价值。让我们一步步思考：

1. 首先，分析指数的编制规则和成分股特点
2. 然后，对比同类ETF的费率和流动性
3. 接着，评估当前估值水平和历史分位
4. 再次，考虑宏观经济和政策因素
5. 最后，给出综合评价和配置建议

请按照以上步骤逐一分析。
```"""
    },
    {
        "id": "bp_fewshot",
        "category": "技巧 (Techniques)",
        "title": "少样本提示 (Few-Shot Prompting)",
        "content": """**提供 1-3 个高质量的输入输出示例，让模型快速理解你的意图、格式和风格。**

---
📋 **资管行业示例：**

```
请按照以下格式分析研报要点：

【示例 1】
研报：《人工智能行业深度报告》
要点：
- 核心观点：AI 行业进入商业化加速期
- 关键数据：2024年市场规模预计达 5000 亿
- 投资建议：关注算力和应用层龙头

【示例 2】
研报：《新能源车月度跟踪》
要点：
- 核心观点：渗透率持续提升
- 关键数据：11月销量同比增长 35%
- 投资建议：整车和电池环节值得关注

【待分析】
研报：《公募基金行业2024展望》
要点：
```"""
    },
    {
        "id": "bp_role",
        "category": "技巧 (Techniques)",
        "title": "角色扮演 (Role Prompting)",
        "content": """**明确指定 AI 的角色，可以激活模型中相关的专业知识和语言风格。**

---
📋 **对比示例：**

❌ **差的提示词**：
```
分析一下招商中证A500 ETF
```

✅ **好的提示词**：
```
你是一位拥有 CFA 认证、专注于被动投资的资深分析师，
服务于国内头部基金公司的 FOF 团队。

请从以下维度分析招商中证A500 ETF：
1. 指数特点与成分股分布
2. 费率与流动性评估
3. 跟踪误差与运作效率
4. 与沪深300/中证500的差异化

请使用专业术语，数据详实，结论清晰。
```"""
    },

    # Tips
    {
        "id": "bp_delimiters",
        "category": "小贴士 (Tips)",
        "title": "使用分隔符",
        "content": """**使用分隔符清晰地区分指令和数据，防止提示词注入。**

常用分隔符：
- 三个引号: `'''` 或 `\"\"\"`
- XML 标签: `<text></text>`
- 破折号: `---`

---
📋 **资管行业示例：**

```
请总结以下研报的核心观点：

<研报内容>
{这里粘贴研报全文}
</研报内容>

输出格式：
1. 一句话概括
2. 3-5 个要点
3. 投资建议
```"""
    },
    {
        "id": "bp_clarity",
        "category": "小贴士 (Tips)",
        "title": "具体与清晰",
        "content": """**避免模糊的指令。多使用形容词、副词和具体的约束条件。**

---
📋 **对比示例：**

❌ **差**：
```
写一篇关于基金的文章
```

✅ **好**：
```
撰写一篇 800 字的科普文章，主题是"什么是 ETF"。
要求：
- 目标读者：投资入门新手
- 语言风格：通俗易懂，避免专业术语
- 结构：开篇引入、概念解释、优势分析、注意事项
- 多用比喻（如"一篮子股票"）帮助理解
- 结尾加入行动号召
```"""
    },
    {
        "id": "bp_output_format",
        "category": "小贴士 (Tips)",
        "title": "指定输出格式",
        "content": """**明确指定期望的输出格式，可以获得更结构化的结果。**

---
📋 **常用输出格式：**

```
# Markdown 格式
请以 Markdown 格式输出，包含标题、列表和加粗。

# JSON 格式
请以 JSON 格式输出：{"summary": "", "points": [], "recommendation": ""}

# 表格格式
请以 Markdown 表格形式输出，列包括：名称、代码、涨跌幅、分析。

# 分点格式
请分点列出，每点不超过 50 字。
```"""
    }
]

class PromptManager:
    def __init__(self):
        self.file_path = PROMPTS_FILE
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def _read_prompts(self) -> List[Dict]:
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def _save_prompts(self, prompts: List[Dict]):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(prompts, f, indent=2, ensure_ascii=False)

    def list_prompts(self) -> List[Dict]:
        return self._read_prompts()

    def save_prompt(self, title: str, content: str, tags: List[str] = []) -> Dict:
        prompts = self._read_prompts()
        new_prompt = {
            "id": str(uuid.uuid4()),
            "title": title,
            "content": content,
            "tags": tags,
            "created_at": str(uuid.uuid1())  # Simple timestamp
        }
        prompts.append(new_prompt)
        self._save_prompts(prompts)
        return new_prompt

    def delete_prompt(self, prompt_id: str) -> bool:
        prompts = self._read_prompts()
        initial_len = len(prompts)
        prompts = [p for p in prompts if p['id'] != prompt_id]
        if len(prompts) < initial_len:
            self._save_prompts(prompts)
            return True
        return False

    def update_prompt(self, prompt_id: str, title: str, content: str, tags: List[str] = []) -> Optional[Dict]:
        prompts = self._read_prompts()
        for p in prompts:
            if p['id'] == prompt_id:
                p['title'] = title
                p['content'] = content
                p['tags'] = tags
                self._save_prompts(prompts)
                return p
        return None

    def get_best_practices(self) -> List[Dict]:
        return BEST_PRACTICES

    async def optimize_prompt(self, original_prompt: str, model: str = "general", framework: str = "auto", tone: str = "professional") -> Dict[str, str]:
        """调用 PromptAgent 优化提示词"""
        agent = multi_agent_system.registry.get("提示词智能体")
        if not agent:
            return {"error": "PromptAgent not found."}
        
        # 构建更详细的指令
        instruction = f"""作为一位资深的 Prompt Engineer，请优化以下提示词。

**原始提示词**：
{original_prompt}

**优化要求**：
1. **目标模型**：{model} (针对该模型的特性进行优化)
2. **框架**：{framework if framework != 'auto' else '请选择最适合该任务的框架 (如 CO-STAR, CRISPE, ICIO 等)'}
3. **语气风格**：{tone}

**输出格式**：
请务必返回一个 JSON 格式的字符串（不要包含 Markdown 代码块标记），包含以下字段：
- `optimized_prompt`: 优化后的完整提示词内容。
- `explanation`: 简要说明你做了哪些优化以及为什么（Markdown 格式）。
- `comparison`: 一个简短的对比说明，指出优化前后的主要区别。

如果无法生成 JSON，请直接输出优化后的提示词，但我更希望是 JSON。
"""
        
        response = agent.invoke([HumanMessage(content=instruction)])
        
        # 解析响应
        try:
            # 尝试提取 JSON
            import re
            import json
            json_match = re.search(r'\{.*\}', response.replace('\n', ' '), re.DOTALL)
            if not json_match:
                # 宽松模式
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
            
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    return data
                except:
                    pass
            
            # Fallback
            return {
                "optimized_prompt": response,
                "explanation": "自动解析失败，直接展示模型输出。",
                "comparison": "无"
            }
        except Exception as e:
             return {
                "optimized_prompt": response,
                "explanation": f"解析出错: {str(e)}",
                "comparison": "无"
            }

prompt_manager = PromptManager()
