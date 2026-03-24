"""通用响应模型"""
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar("T")


class ResponseBase(BaseModel):
    """通用响应基类"""
    code: str = "success"
    message: str = "操作成功"


class DataResponse(ResponseBase, Generic[T]):
    """带数据的响应"""
    data: Optional[T] = None


class PageInfo(BaseModel):
    """分页信息"""
    page: int = 1
    page_size: int = 20
    total: int = 0
    total_pages: int = 0


class PaginatedResponse(ResponseBase):
    """分页响应"""
    data: list = []
    page_info: PageInfo = PageInfo()
