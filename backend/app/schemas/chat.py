"""聊天相关模型"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ChatMessage(BaseModel):
    """聊天消息"""
    role: str = Field(..., description="角色: user/assistant/system")
    content: str = Field(..., description="消息内容")
    timestamp: Optional[datetime] = None


class SendMessageRequest(BaseModel):
    """发送消息请求"""
    content: str = Field(..., min_length=1, description="消息内容")
    session_id: Optional[str] = Field(None, description="会话ID，新会话可不传")
    session_type: str = Field(default="goal_discussion", description="会话类型")


class SendMessageResponse(BaseModel):
    """发送消息响应"""
    code: str = "success"
    session_id: str
    message: ChatMessage
    token_used: int = 0  # 本次消耗的 Token


class SessionResponse(BaseModel):
    """会话响应"""
    id: str
    session_type: str
    status: str
    message_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SessionHistory(BaseModel):
    """会话历史"""
    session_id: str
    messages: List[ChatMessage]
