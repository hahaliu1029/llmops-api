import mimetypes
import os
from typing import Any
from injector import inject
from dataclasses import dataclass
from internal.core.tools.builtin_tools.providers import BuiltInProviderManager
from internal.core.tools.builtin_tools.categories import BuiltinCategoryManager
from pydantic import BaseModel
from internal.exception import NotFoundException
from flask import current_app


@inject
@dataclass
class BuiltinToolService:
    """内置工具服务"""

    builtin_provider_manager: BuiltInProviderManager
    builtin_category_manager: BuiltinCategoryManager

    def get_builtin_tools(self) -> list:
        """获取内置工具列表"""
        # 1.获取所有提供商
        providers = self.builtin_provider_manager.get_providers()
        # 2. 遍历所有提供商，获取所有工具
        builtin_tools = []
        for provider in providers:
            provider_entity = provider.provider_entity
            builtin_tool = {**provider_entity.model_dump(exclude=["icon"]), "tools": []}

            for tool_entity in provider.get_tool_entities():
                tool = provider.get_tool(tool_entity.name)
                tool_dict = {
                    **tool_entity.model_dump(),
                    "inputs": self.get_tool_inputs(tool),
                }
                builtin_tool["tools"].append(tool_dict)
            builtin_tools.append(builtin_tool)
        return builtin_tools

    def get_provider_tool(self, provider_name: str, tool_name: str) -> dict:
        """根据提供者名称和工具名称获取工具"""
        # 1.获取提供商
        provider = self.builtin_provider_manager.get_provider(provider_name)
        if provider is None:
            raise NotFoundException(f"提供商{provider_name}不存在")

        # 2.获取工具
        tool_entity = provider.get_tool_entity(tool_name)
        if tool_entity is None:
            raise NotFoundException(f"工具{tool_name}不存在")

        # 组装提供商和工具信息
        provider_entity = provider.provider_entity
        tool = provider.get_tool(tool_name)

        builtin_tool = {
            "provider": provider_entity.model_dump(exclude=["icon", "created_at"]),
            **tool_entity.model_dump(),
            "created_at": provider_entity.created_at,
            "inputs": self.get_tool_inputs(tool),
        }
        return builtin_tool

    def get_provider_icon(self, provider_name: str) -> tuple[bytes, str]:
        """获取提供商图标"""
        provider = self.builtin_provider_manager.get_provider(provider_name)
        if provider is None:
            raise NotFoundException(f"提供商{provider_name}不存在")
        # 获取项目的根路径信息
        root_path = os.path.dirname(os.path.dirname(current_app.root_path))

        # 拼接得到提供商图标的文件夹
        provider_path = os.path.join(
            root_path,
            "internal/core/tools/builtin_tools/providers",
            provider_name,
        )

        # 获取提供商图标的路径
        icon_path = os.path.join(provider_path, "_asset", provider.provider_entity.icon)

        # 检测图标是否存在
        if not os.path.exists(icon_path):
            raise NotFoundException(f"提供商{provider_name}的图标不存在")

        # 读取icon的类型
        mimetype, _ = mimetypes.guess_type(icon_path)
        mimetype = mimetype or "application/octet-stream"

        # 读取icon的内容
        with open(icon_path, "rb") as f:
            icon = f.read()
        return icon, mimetype

    def get_categories(self) -> list[str, Any]:
        """获取所有内置提供商的分类信息"""
        category_map = self.builtin_category_manager.get_category_map()
        return [
            {
                "name": category["entity"].name,
                "category": category["entity"].category,
                "icon": category["icon"],
            }
            for category in category_map.values()
        ]

    @classmethod
    def get_tool_inputs(cls, tool) -> list:
        """获取工具输入参数"""
        inputs = []
        if hasattr(tool, "args_schema") and issubclass(tool.args_schema, BaseModel):
            for field_name, model_field in tool.args_schema.__fields__.items():
                inputs.append(
                    {
                        "name": field_name,
                        "description": model_field.description or "",
                        "required": model_field.is_required(),
                        "type": (
                            model_field.annotation.__name__
                            if model_field.annotation
                            else "Any"
                        ),
                    }
                )
        return inputs
