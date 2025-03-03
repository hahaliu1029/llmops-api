from datetime import datetime
import hashlib
import importlib
from typing import Any, List
from langchain_core.documents import Document


def dynamic_import(module_name: str, symbol_name: str) -> Any:
    """动态导入模块"""
    module = importlib.import_module(module_name)
    return getattr(module, symbol_name)  # 获取模块的属性


def add_attribute(attr_name: str, attr_value: Any):
    """装饰器函数，用于为函数添加属性，第一个参数为属性名，第二个参数为属性值"""

    def decorator(func):
        setattr(func, attr_name, attr_value)
        return func

    return decorator


def generate_text_hash(text: str) -> str:
    """生成文本的hash值"""
    # 将需要计算的内容加上None，防止传入空字符串时报错
    text = str(text) + "None"
    return hashlib.sha3_256(text.encode()).hexdigest()


def datetime_to_timestamp(dt: datetime) -> int:
    """将datetime类型转换为时间戳，如果数据不存在则返回0"""
    if dt is None:
        return 0
    return int(dt.timestamp())


def combine_documents(documents: list[Document]) -> str:
    """将对应的文档列表使用换行符进行合并"""
    return "\n\n".join([document.page_content for document in documents])
