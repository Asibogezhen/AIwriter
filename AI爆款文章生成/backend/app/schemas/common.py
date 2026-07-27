"""通用请求/响应模型"""

from typing import Optional, Any, Generic, TypeVar
from pydantic import BaseModel


class DeleteRequest(BaseModel):
    id: str


class PageRequest(BaseModel):
    current: int = 1
    page_size: int = 10
    sort_field: str = "created_at"
    sort_order: str = "desc"


T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "success"
    data: Optional[T] = None

    @classmethod
    def success(cls, data: Any = None, message: str = "success"):
        return cls(code=0, message=message, data=data)

    @classmethod
    def error(cls, code: int, message: str):
        return cls(code=code, message=message, data=None)
