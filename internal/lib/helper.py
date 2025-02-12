import importlib
from typing import Any


def dynamic_import(module_name: str, symbol_name: str) -> Any:
    """动态导入模块"""
    module = importlib.import_module(module_name)
    return getattr(module, symbol_name)  # 获取模块的属性
