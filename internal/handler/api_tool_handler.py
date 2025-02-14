from uuid import UUID
from injector import inject
from dataclasses import dataclass
from flask import request
from internal.schema.api_tool_schema import (
    ValidateOpenAPISchemaReq,
    CreateApiToolReq,
    GetApiToolProviderResp,
    GetApiToolResp,
    GetApiToolProvidersWithPageReq,
    GetApiToolProvidersWithPageResp,
    UpdateApiToolProviderReq,
)
from pkg.response import validate_error_json, success_message, success_json
from internal.service import ApiToolService
from pkg.paginator import PageModel


@inject
@dataclass
class ApiToolHandler:
    """自定义API工具处理器"""

    api_tool_service: ApiToolService

    def get_api_tool_providers_with_page(self):
        """获取API工具提供者列表信息，该接口支持分页"""
        req = GetApiToolProvidersWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        # 调用服务获取API工具提供者列表信息
        api_tool_providers, paginator = (
            self.api_tool_service.get_api_tool_providers_with_page(req)
        )

        # 构建响应数据
        resp = GetApiToolProvidersWithPageResp(
            many=True,
        )

        return success_json(
            PageModel(resp.dump(api_tool_providers), paginator=paginator)
        )

    def create_api_tool(self):
        """创建自定义API工具"""
        # 提取请求数据并校验
        req = CreateApiToolReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 调用服务创建自定义API工具
        self.api_tool_service.create_api_tool(req)

        # 返回成功信息
        return success_message("自定义API工具创建成功")

    def update_api_tool_provider(self, provider_id: UUID):
        """更新API工具提供者"""
        req = UpdateApiToolProviderReq()
        if not req.validate():
            return validate_error_json(req.errors)

        self.api_tool_service.update_api_tool_provider(provider_id, req)

        return success_message("API工具提供者更新成功")

    def get_api_tool(self, provider_id: UUID, tool_name: str):
        """根据传递的provider_id和tool_name获取API工具"""
        api_tool = self.api_tool_service.get_api_tool(provider_id, tool_name)

        resp = GetApiToolResp()

        return success_json(resp.dump(api_tool))

    def get_api_tool_provider(self, provider_id: UUID):
        """根据传递的provider_id获取API工具提供者"""
        api_tool_provider = self.api_tool_service.get_api_tool_provider(provider_id)

        resp = GetApiToolProviderResp()

        return success_json(resp.dump(api_tool_provider))

    def delete_api_tool_provider(self, provider_id: UUID):
        """根据传递的provider_id删除API工具提供者"""
        self.api_tool_service.delete_api_tool_provider(provider_id)

        return success_message("API工具提供者删除成功")

    def validate_openapi_schema(self):
        """校验传递的openapi_schema字符串是否正确"""
        # 1.提取前端的数据并校验
        req = ValidateOpenAPISchemaReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.调用并解析传递的数据
        self.api_tool_service.parse_openapi_schema(req.openapi_schema.data)

        # 3.返回成功信息
        return success_message("数据校验成功")
