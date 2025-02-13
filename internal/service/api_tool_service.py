import json
from typing import Any
from injector import inject
from dataclasses import dataclass

from internal.exception import ValidateErrorException
from internal.core.tools.api_tools.entities import OpenAPISchema
from internal.schema.api_tool_schema import CreateApiToolReq
from pkg.sqlalchemy import SQLAlchemy
from internal.model import ApiToolProvider, ApiTool


@inject
@dataclass
class ApiToolService:
    """自定义API插件服务"""

    db: SQLAlchemy

    def create_api_tool(self, req: CreateApiToolReq) -> None:
        """根据传递的请求创建自定义API工具"""
        # todo:等待授权认证模块完成后再进行开发
        account_id = "15fd2840-e294-4413-83d0-e083e9a7bc6b"

        # 检验并提取openapi_schema对应的数据
        print("req.openapi_schema", req.openapi_schema.data)
        openapi_schema = self.parse_openapi_schema(req.openapi_schema.data)

        # 查询当前用户是否已经存在同名的工具提供者，如果是则抛出异常
        api_tool_provider = (
            self.db.session.query(ApiToolProvider)
            .filter_by(account_id=account_id, name=req.name.data)
            .one_or_none()
        )
        if api_tool_provider:
            raise ValidateErrorException(
                f"当前用户已经存在名为{req.name.data}的API工具提供者"
            )

        # 开启数据库自动提交
        with self.db.auto_commit():
            # 先创建API工具提供者，并获取其ID，然后创建API工具
            api_tool_provider = ApiToolProvider(
                account_id=account_id,
                name=req.name.data,
                icon=req.icon.data,
                description=openapi_schema.description,
                openapi_schema=req.openapi_schema.data,
                headers=req.headers.data,
            )
            self.db.session.add(api_tool_provider)
            self.db.session.flush()

            # 创建api工具并关联api_tool_provider
            for path, path_item in openapi_schema.paths.items():
                for method, method_item in path_item.items():
                    api_tool = ApiTool(
                        account_id=account_id,
                        provider_id=api_tool_provider.id,
                        name=method_item.get("operationId"),
                        description=method_item.get("description"),
                        url=f"{openapi_schema.server}{path}",
                        method=method,
                        parameters=method_item.get("parameters", []),
                    )
                    self.db.session.add(api_tool)

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
