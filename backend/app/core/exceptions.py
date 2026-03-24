"""自定义异常"""
from fastapi import HTTPException, status


class AppException(HTTPException):
    """应用基础异常"""
    def __init__(self, detail: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        super().__init__(status_code=status_code, detail=detail)


class AuthenticationError(AppException):
    """认证错误"""
    def __init__(self, detail: str = "认证失败"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class AuthorizationError(AppException):
    """授权错误"""
    def __init__(self, detail: str = "权限不足"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class NotFoundError(AppException):
    """资源不存在"""
    def __init__(self, detail: str = "资源不存在"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ValidationError(AppException):
    """验证错误"""
    def __init__(self, detail: str = "数据验证失败"):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


class TokenQuotaExceededError(AppException):
    """Token 配额超限"""
    def __init__(self, detail: str = "Token 配额已用完，请升级会员"):
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail)


class AIResponseError(AppException):
    """AI 响应错误"""
    def __init__(self, detail: str = "AI 服务响应失败"):
        super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)
