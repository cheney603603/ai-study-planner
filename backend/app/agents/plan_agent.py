"""计划生成 Agent"""
from typing import Dict, Any
from app.agents.base import BaseAgent


class PlanAgent(BaseAgent):
    """计划生成 Agent - 生成个性化学习计划"""
    
    def __init__(self):
        super().__init__(
            name="plan_agent",
            description="生成个性化学习计划"
        )
    
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成学习计划
        
        1. 汇总收集的信息
        2. 调用 LLM 生成计划
        3. 格式化输出
        """
        collected_info = context.get("collected_info", {})
        session_id = context.get("session_id")
        
        self.log("info", f"开始生成计划: session={session_id}")
        
        # 构建提示词
        prompt = self._build_prompt(collected_info)
        
        # 调用 LLM（TODO: 实际调用）
        llm_result = await self._call_llm(prompt)
        
        # 解析和格式化计划
        plan = self._parse_plan(llm_result["response"], collected_info)
        
        self.log("info", f"计划生成完成: {len(plan.get('phases', []))} 个阶段")
        
        return {
            "response": self._format_plan_response(plan),
            "token_used": llm_result.get("token_used", 200),
            "metadata": {
                "plan": plan,
                "ready_to_save": True
            }
        }
    
    def _build_prompt(self, info: dict) -> str:
        """构建 LLM 提示词"""
        return f"""
请为以下学习需求生成一个详细的学习计划：

学习主题：{info.get('subject', '待定')}
学习目标：{info.get('target', '待定')}
每日可用时间：{info.get('daily_duration', 60)} 分钟
期望完成时间：{info.get('deadline', '待定')}

请生成包含以下内容的计划：
1. 总体学习路径（分几个阶段）
2. 每个阶段的名称和目标
3. 每日任务安排
4. 预估完成时间

请用 JSON 格式返回。
"""
    
    def _parse_plan(self, llm_response: str, info: dict) -> dict:
        """
        解析 LLM 返回的计划
        
        TODO: 实际解析 JSON，添加验证和 fallback
        """
        # 开发阶段返回示例计划
        return {
            "title": f"{info.get('subject', '学习')}学习计划",
            "subject": info.get("subject", "通用学习"),
            "target": info.get("target", "掌握相关知识"),
            "daily_duration": info.get("daily_duration", 60),
            "phases": [
                {
                    "name": "第一阶段：基础入门",
                    "duration_days": 14,
                    "goals": ["了解基本概念", "掌握基础操作"],
                    "daily_tasks": 2
                },
                {
                    "name": "第二阶段：进阶提升",
                    "duration_days": 21,
                    "goals": ["深入理解原理", "实践应用"],
                    "daily_tasks": 3
                },
                {
                    "name": "第三阶段：实战巩固",
                    "duration_days": 14,
                    "goals": ["完成项目实战", "总结复盘"],
                    "daily_tasks": 3
                }
            ],
            "total_days": 49,
            "estimated_completion": "7周"
        }
    
    def _format_plan_response(self, plan: dict) -> str:
        """格式化计划响应"""
        response = f"📋 **学习计划已生成！**\n\n"
        response += f"**《{plan['title']}》**\n\n"
        response += f"⏱️ 预计总时长：{plan.get('estimated_completion', '待定')}\n"
        response += f"📆 总天数：{plan.get('total_days', 0)} 天\n\n"
        response += "**📚 学习阶段：**\n\n"
        
        for i, phase in enumerate(plan.get("phases", []), 1):
            response += f"{i}. **{phase['name']}** ({phase['duration_days']}天)\n"
            response += f"   - 目标：{', '.join(phase.get('goals', []))}\n"
            response += f"   - 每日任务：约 {phase.get('daily_tasks', 2)} 个\n\n"
        
        response += "是否确认此计划？确认后我将为你创建详细的学习任务。"
        
        return response
