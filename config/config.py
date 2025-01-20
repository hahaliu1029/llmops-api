import os
from typing import Any
from .default_config import DEFAULT_CONFIG


def _get_env(key: str) -> Any:
    """获取环境变量"""
    return os.getenv(key, DEFAULT_CONFIG.get(key))


def _get_bool_env(key: str) -> bool:
    """获取环境变量"""
    value: str = _get_env(key)
    print("*******")
    print(value)
    return value.lower() == "true" if value else False


class Config:
    def __init__(self):
        self.WTF_CSRF_ENABLED = _get_bool_env("WTF_CSRF_ENABLED")

        print("********")
        print(self.WTF_CSRF_ENABLED)

        # 数据库配置
        self.SQLALCHEMY_DATABASE_URI = _get_env("SQLALCHEMY_DATABASE_URI")
        self.SQLALCHEMY_ENGINE_OPTIONS = {
            # "pool_pre_ping": True,
            "pool_recycle": int(_get_env("SQLALCHEMY_POOL_RECYCLE")),
            "pool_size": int(_get_env("SQLALCHEMY_POOL_SIZE")),
            # "max_overflow": 10,
        }
        self.SQLALCHEMY_ECHO = _get_bool_env("SQLALCHEMY_ECHO")
