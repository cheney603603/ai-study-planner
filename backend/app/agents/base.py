"""Agent 基类"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.core.logging import get_logger


class BaseAgent(ABC):
    """Agent 基类"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.logger = get_logger(f"agents.{name}")
    
    @abstractmethod
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理输入，返回结果
        
        Args:
            context: 包含以下键的字典:
                - user_id: 用户ID
                - message: 用户消息
                - session_id: 会话ID
                - history: 历史消息
        
        Returns:
            包含以下键的字典:
                - response: Agent 响应文本
                - token_used: 消耗的 token 数
                - metadata: 额外的元数据
        """
        pass
    
    async def _call_llm(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        调用 LLM
        
        TODO: 实现实际的 LLM 调用
        """
        # TODO: 调用 DashScope API
        # 当前返回 mock 响应
        self.logger.info(f"调用 LLM: {prompt[:50]}...")
        
        return {
            "response": f"[Mock] Agent {self.name} 处理了: {prompt[:30]}...",
            "token_used": 100
        }
    
    def log(self, level: str, message: str, **kwargs):
        """日志记录"""
        extra = {"agent": self.name}
        extra.update(kwargs)
        getattr(self.logger, level)(message, extra=extra)
