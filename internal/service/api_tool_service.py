import json
from typing import Any
from injector import inject
from dataclasses import dataclass
from internal.exception import ValidateErrorException
from internal.core.tools.api_tools.entities import OpenAPISchema


@inject
@dataclass
class ApiToolService:
    """自定义API插件服务"""

    @classmethod
    def parse_openapi_schema(cls, openapi_schema_str: str) -> OpenAPISchema:
        """解析传递的openapi_schema字符串， 如果出错则抛出错误"""
        try:
            data = json.loads(openapi_schema_str.strip())
            if not isinstance(data, dict):
                raise
        except Exception as e:
            raise ValidateErrorException("传递数据必须符合OpenAPI规范")

        return OpenAPISchema(**data)
