from dataclasses import field, dataclass
from typing import Any
from flask import jsonify

from .http_code import HttpCode


@dataclass
class Response:
    """基础HTTP响应类"""

    code: HttpCode = HttpCode.SUCCESS
    message: str = ""
    data: Any = field(default_factory=dict)


def json(data: Response = None):
    """基础的响应函数"""
    if data is None:
        data = Response()

    return jsonify(data)


def success_json(data: Any = None, message: str = ""):
    """成功响应"""
    return json(Response(code=HttpCode.SUCCESS, message=message, data=data))


def fail_json(data: Any = None, message: str = ""):
    """失败响应"""
    return json(Response(code=HttpCode.FAIL, message=message, data=data))


def validate_error_json(errors: dict = None):
    """验证错误"""
    first_key = next(iter(errors))
    if first_key is not None:
        message = errors.get(first_key)[0]
    else:
        message = "参数错误"
    return json(Response(code=HttpCode.VALIDATE_ERROR, message=message, data=errors))


def message(code: HttpCode = None, message: str = ""):
    """基础消息响应"""
    return json(Response(code=code, message=message, data={}))


def success_message(message: str = ""):
    """成功消息"""
    return message(code=HttpCode.SUCCESS, message=message)


def fail_message(message: str = ""):
    """失败消息"""
    return message(code=HttpCode.FAIL, message=message)


def not_found_message(message: str = ""):
    """未找到"""
    return message(code=HttpCode.NOT_FOUND, message=message)


def unauthorized_message(message: str = ""):
    """未授权"""
    return message(code=HttpCode.UNAUTHORIZED, message=message)


def forbidden_message(message: str = ""):
    """禁止"""
    return message(code=HttpCode.FORBIDDEN, message=message)
