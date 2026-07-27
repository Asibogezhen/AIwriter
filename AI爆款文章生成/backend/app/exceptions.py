"""业务异常定义"""

from enum import Enum


class ErrorCode(Enum):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message

    SUCCESS = (0, "成功")
    PARAMS_ERROR = (10400, "请求参数错误")
    UNAUTHORIZED = (10401, "未登录")
    FORBIDDEN = (10403, "无权限")
    NOT_FOUND = (10404, "资源不存在")
    CONFLICT = (10409, "冲突")
    QUOTA_EXCEEDED = (10429, "额度不足")
    SYSTEM_ERROR = (10500, "系统内部异常")


class BusinessException(Exception):
    def __init__(self, error_code: ErrorCode, message: str = ""):
        self.error_code = error_code
        self.message = message or error_code.message


def throw_if(condition: bool, error_code: ErrorCode, message: str = ""):
    if condition:
        raise BusinessException(error_code, message)
