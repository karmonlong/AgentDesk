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

*示例：*
请作为一名资深的数据分析师（Context），帮我分析这份销售报表（Objective）。请使用专业、客观的风格（Style/Tone），面向公司管理层（Audience），输出一份 Markdown 格式的分析报告，包含关键发现和建议（Response）。"""
    },
    {
        "id": "bp_crispe",
        "category": "框架 (Frameworks)",
        "title": "CRISPE 框架",
        "content": """**CRISPE 框架强调角色的设定和能力的定义。**

**C - Capacity (能力)**: 设定 AI 的角色（如"你是一个资深的 Python 程序员"）。
**R - Role (角色)**: 进一步细化角色和视角。
**I - Insight (洞察)**: 提供必要的背景信息和上下文。
**S - Statement (陈述)**: 明确具体的任务指令。
**P - Personality (个性)**: 设定回复的风格。
**E - Experiment (尝试)**: 要求 AI 提供多个选项供选择（可选）。"""
    },
    {
        "id": "bp_broke",
        "category": "框架 (Frameworks)",
        "title": "BROKE 框架",
        "content": """**BROKE 框架适用于需要迭代优化的任务。**

**B - Background (背景)**: 陈述背景。
**R - Role (角色)**: 设定角色。
**O - Objective (目标)**: 设定目标。
**K - Key Result (关键结果)**: 定义成功的标准。
**E - Evolve (进化)**: 根据反馈进行调整。"""
    },
    
    # Techniques
    {
        "id": "bp_cot",
        "category": "技巧 (Techniques)",
        "title": "思维链 (Chain of Thought)",
        "content": """**通过引导模型展示推理过程，显著提高复杂逻辑推理、数学计算和决策任务的准确率。**

**方法 1 (Zero-Shot)**: 在提示词末尾加上 *"Let's think step by step"* (让我们一步步思考)。
**方法 2 (Few-Shot)**: 提供展示推理步骤的示例。

*适用场景：* 数学题、逻辑推理、代码调试、复杂决策。"""
    },
    {
        "id": "bp_fewshot",
        "category": "技巧 (Techniques)",
        "title": "少样本提示 (Few-Shot Prompting)",
        "content": """**提供 1-3 个高质量的输入输出示例，让模型快速理解你的意图、格式和风格。**

*示例：*
将以下评论分类为正面、负面或中性：

评论：这个产品太棒了！
情感：正面

评论：快递太慢了，包装也破了。
情感：负面

评论：价格还行，但颜色有点色差。
情感："""
    },
    {
        "id": "bp_role",
        "category": "技巧 (Techniques)",
        "title": "角色扮演 (Role Prompting)",
        "content": """**明确指定 AI 的角色，可以激活模型中相关的专业知识和语言风格。**

*差的提示词*：写一个贪吃蛇游戏。
*好的提示词*：你是一位拥有 10 年经验的资深 Python 游戏开发者，请使用 Pygame 库编写一个结构良好、注释清晰的贪吃蛇游戏。"""
    },

    # Tips
    {
        "id": "bp_delimiters",
        "category": "小贴士 (Tips)",
        "title": "使用分隔符",
        "content": """**使用分隔符清晰地区分指令和数据，防止提示词注入，并帮助模型更好地解析输入。**

常用分隔符：
- 三个引号: `'''` 或 `\"\"\"`
- XML 标签: `<text></text>`
- 破折号: `---`

*示例：*
请总结被三个引号包含的文本内容：
\"\"\"
这里是需要总结的文章内容...
\"\"\""""
    },
    {
        "id": "bp_clarity",
        "category": "小贴士 (Tips)",
        "title": "具体与清晰",
        "content": """**避免模糊的指令。多使用形容词、副词和具体的约束条件。**

*差*：写一篇关于 AI 的文章。
*好*：写一篇 500 字的科普文章，介绍生成式 AI 的工作原理，目标读者是高中生，语言要通俗易懂，多用比喻。"""
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
