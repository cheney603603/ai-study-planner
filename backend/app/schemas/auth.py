"""认证相关模型"""
from pydantic import BaseModel, Field
from typing import Optional


class SendCodeRequest(BaseModel):
    """发送验证码请求"""
    phone: str = Field(..., min_length=11, max_length=20, description="手机号")


class SendCodeResponse(BaseModel):
    """发送验证码响应"""
    code: str = "success"
    message: str = "验证码已发送"
    expire_seconds: int = 300  # 验证码有效期


class LoginRequest(BaseModel):
    """登录请求"""
    phone: str = Field(..., description="手机号")
    code: str = Field(..., min_length=4, max_length=6, description="验证码")


class LoginResponse(BaseModel):
    """登录响应"""
    code: str = "success"
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # 有效期（秒）
    user: Optional["UserInfo"] = None


class UserInfo(BaseModel):
    """用户信息"""
    id: str
    phone: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    level: str = "入门"
    total_score: int = 0
    
    class Config:
        from_attributes = True


class TokenUsage(BaseModel):
    """Token 用量"""
    quota: int  # 配额
    used: int  # 已用
    remaining: int  # 剩余
    reset_date: Optional[str] = None  # 重置日期
