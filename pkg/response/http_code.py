from enum import Enum


class HttpCode(str, Enum):
    """HTTP status codes."""

    SUCCESS = "success"  # 成功
    FAIL = "fail"  # 失败
    NOT_FOUND = "not_found"  # 未找到
    UNAUTHORIZED = "unauthorized"  # 未授权
    FORBIDDEN = "forbidden"  # 禁止
    VALIDATE_ERROR = "validate_error"  # 验证错误
