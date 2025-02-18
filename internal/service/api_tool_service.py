import json
from uuid import UUID
from typing import Any
from injector import inject
from dataclasses import dataclass

from internal.exception import ValidateErrorException, NotFoundException
from internal.core.tools.api_tools.entities import OpenAPISchema
from internal.schema.api_tool_schema import (
    CreateApiToolReq,
    GetApiToolProvidersWithPageReq,
    UpdateApiToolProviderReq,
)
from pkg.sqlalchemy import SQLAlchemy
from pkg.paginator import Paginator
from internal.model import ApiToolProvider, ApiTool
from sqlalchemy import desc
from .base_service import BaseService
from internal.core.tools.api_tools.providers import ApiProvidersManager


@inject
@dataclass
class ApiToolService(BaseService):
    """自定义API插件服务"""

    db: SQLAlchemy
    api_providers_manager: ApiProvidersManager

    def update_api_tool_provider(
        self, provider_id: UUID, req: UpdateApiToolProviderReq
    ) -> None:
        """更新API工具提供者"""
        # todo:等待授权认证模块完成后再进行开发
        account_id = "15fd2840-e294-4413-83d0-e083e9a7bc6b"

        # 先查找数据，检测是否存在，权限是否正确
        api_tool_provider = self.get(primary_key=provider_id, model=ApiToolProvider)
        # api_tool_provider = self.db.session.query(ApiToolProvider).get(provider_id)

        if not api_tool_provider or str(api_tool_provider.account_id) != account_id:
            raise NotFoundException("API工具提供者不存在")

        # 检验并提取openapi_schema对应的数据
        openapi_schema = self.parse_openapi_schema(req.openapi_schema.data)

        # 检测当前用户是否已经存在同名的工具提供者，如果是则抛出异常
        check_api_tool_provider = (
            self.db.session.query(ApiToolProvider)
            .filter(
                ApiToolProvider.account_id == account_id,
                ApiToolProvider.name == req.name.data,
                ApiToolProvider.id != provider_id,
            )
            .one_or_none()
        )
        if check_api_tool_provider:
            raise ValidateErrorException(
                f"当前用户已经存在名为{req.name.data}的API工具提供者"
            )

        # 开启数据库自动提交
        with self.db.auto_commit():
            # 先删除该工具提供者下的所有工具
            self.db.session.query(ApiTool).filter(
                ApiTool.provider_id == provider_id, ApiTool.account_id == account_id
            ).delete()

            # 更新API工具提供者
            self.update(
                api_tool_provider,
                name=req.name.data,
                icon=req.icon.data,
                openapi_schema=req.openapi_schema.data,
                headers=req.headers.data,
                description=openapi_schema.description,
            )
            # api_tool_provider.name = req.name.data
            # api_tool_provider.icon = req.icon.data
            # # api_tool_provider.description = openapi_schema.description
            # api_tool_provider.openapi_schema = req.openapi_schema.data
            # api_tool_provider.headers = req.headers.data

            # 创建api工具并关联api_tool_provider
            for path, path_item in openapi_schema.paths.items():
                for method, method_item in path_item.items():
                    self.create(
                        ApiTool,
                        account_id=account_id,
                        provider_id=api_tool_provider.id,
                        name=method_item.get("operationId"),
                        description=method_item.get("description"),
                        url=f"{openapi_schema.server}{path}",
                        method=method,
                        parameters=method_item.get("parameters", []),
                    )
                    # api_tool = ApiTool(
                    #     account_id=account_id,
                    #     provider_id=api_tool_provider.id,
                    #     name=method_item.get("operationId"),
                    #     description=method_item.get("description"),
                    #     url=f"{openapi_schema.server}{path}",
                    #     method=method,
                    #     parameters=method_item.get("parameters", []),
                    # )
                    # self.db.session.add(api_tool)

    def get_api_tool_providers_with_page(
        self, req: GetApiToolProvidersWithPageReq
    ) -> tuple[list[Any], Paginator]:
        """获取自定义API工具提供者列表信息，支持分页"""
        # todo:等待授权认证模块完成后再进行开发
        account_id = "15fd2840-e294-4413-83d0-e083e9a7bc6b"

        # 构建分页查询器
        paginator = Paginator(self.db, req)
        # 构建筛选器
        filters = [ApiToolProvider.account_id == account_id]
        if req.search_word.data:
            filters.append(ApiToolProvider.name.ilike(f"%{req.search_word.data}%"))
        # 执行分页并获取数据
        api_tool_providers = paginator.paginate(
            self.db.session.query(ApiToolProvider)
            .filter(*filters)
            .order_by(desc("created_at"))
        )

        return api_tool_providers, paginator

    def get_api_tool(self, provider_id: UUID, tool_name: str) -> ApiTool:
        """根据传递的provider_id和tool_name获取API工具"""
        # todo:等待授权认证模块完成后再进行开发
        account_id = "15fd2840-e294-4413-83d0-e083e9a7bc6b"

        api_tool = (
            self.db.session.query(ApiTool)
            .filter_by(provider_id=provider_id, name=tool_name)
            .one_or_none()
        )
        if not api_tool or str(api_tool.account_id) != account_id:
            raise NotFoundException("API工具不存在")

        return api_tool

    def get_api_tool_provider(self, provider_id: UUID) -> ApiToolProvider:
        """根据传递的provider_id获取API工具提供者"""
        # todo:等待授权认证模块完成后再进行开发
        account_id = "15fd2840-e294-4413-83d0-e083e9a7bc6b"

        api_tool_provider = self.get(primary_key=provider_id, model=ApiToolProvider)
        # api_tool_provider = self.db.session.query(ApiToolProvider).get(provider_id)
        if not api_tool_provider or str(api_tool_provider.account_id) != account_id:
            raise NotFoundException("API工具提供者不存在")

        return api_tool_provider

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
        # with self.db.auto_commit():
        # 先创建API工具提供者，并获取其ID，然后创建API工具
        api_tool_provider = self.create(
            ApiToolProvider,
            account_id=account_id,
            name=req.name.data,
            icon=req.icon.data,
            description=openapi_schema.description,
            openapi_schema=req.openapi_schema.data,
            headers=req.headers.data,
        )
        # api_tool_provider = ApiToolProvider(
        #     account_id=account_id,
        #     name=req.name.data,
        #     icon=req.icon.data,
        #     description=openapi_schema.description,
        #     openapi_schema=req.openapi_schema.data,
        #     headers=req.headers.data,
        # )
        # self.db.session.add(api_tool_provider)
        # self.db.session.flush()

        # 创建api工具并关联api_tool_provider
        for path, path_item in openapi_schema.paths.items():
            for method, method_item in path_item.items():
                self.create(
                    ApiTool,
                    account_id=account_id,
                    provider_id=api_tool_provider.id,
                    name=method_item.get("operationId"),
                    description=method_item.get("description"),
                    url=f"{openapi_schema.server}{path}",
                    method=method,
                    parameters=method_item.get("parameters", []),
                )
                # api_tool = ApiTool(
                #     account_id=account_id,
                #     provider_id=api_tool_provider.id,
                #     name=method_item.get("operationId"),
                #     description=method_item.get("description"),
                #     url=f"{openapi_schema.server}{path}",
                #     method=method,
                #     parameters=method_item.get("parameters", []),
                # )
                # self.db.session.add(api_tool)

    def delete_api_tool_provider(self, provider_id: UUID) -> None:
        """根据传递的provider_id删除API工具提供者 + API工具"""
        # todo:等待授权认证模块完成后再进行开发
        account_id = "15fd2840-e294-4413-83d0-e083e9a7bc6b"

        # 先查找数据，检测是否存在，权限是否正确
        api_tool_provider = self.get(primary_key=provider_id, model=ApiToolProvider)
        # api_tool_provider = self.db.session.query(ApiToolProvider).get(provider_id)

        if not api_tool_provider or str(api_tool_provider.account_id) != account_id:
            raise NotFoundException("API工具提供者不存在")

        # 开启数据库自动提交
        with self.db.auto_commit():
            # 删除API工具
            self.db.session.query(ApiTool).filter(
                ApiTool.provider_id == provider_id, ApiTool.account_id == account_id
            ).delete()
            # 删除API工具提供者
            self.db.session.delete(api_tool_provider)

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

    def api_tool_invoke(self):
        provider_id = "d6973469-c231-4cb8-a16e-0a8e94c708c1"
        tool_name = "YoudaoSuggest"

        api_tool = (
            self.db.session.query(ApiTool)
            .filter(ApiTool.provider_id == provider_id, ApiTool.name == tool_name)
            .one_or_none()
        )
        print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
        print("api_tool", api_tool)
        api_tool_provider = api_tool.provider
        print("api_tool_provider", api_tool_provider)

        from internal.core.tools.api_tools.entities import ToolEntity

        tool = self.api_providers_manager.get_tool(
            ToolEntity(
                id=provider_id,
                name=tool_name,
                url=api_tool.url,
                method=api_tool.method,
                description=api_tool.description,
                headers=api_tool_provider.headers,
                parameters=api_tool.parameters,
            )
        )

        return tool.invoke(
            {
                "q": "hello",
                "doctype": "json",
            }
        )
