import yaml
import os
from typing import Any
from injector import inject, singleton
from internal.core.tools.builtin_tools.entities import ProviderEntity, Provider
from pydantic import BaseModel, Field


@inject
@singleton
class BuiltInProviderManager(BaseModel):
    """服务提供商工厂类"""

    provider_map: dict[str, Provider] = Field(default_factory=dict)

    def __init__(self, **kwargs):
        """构造函数，初始化工具提供商映射"""
        super().__init__(**kwargs)
        self._get_provider_tool_map()

    def get_provider(self, provider_name: str) -> Provider:
        """根据提供商名称获取提供商"""
        return self.provider_map.get(provider_name)

    def get_providers(self) -> list[Provider]:
        """获取所有的提供商"""
        return list(self.provider_map.values())

    def get_provider_entities(self) -> list[ProviderEntity]:
        """获取所有的提供商实体"""
        return [provider.provider_entity for provider in self.provider_map.values()]

    def get_tool(self, provider_name: str, tool_name: str) -> Any:
        """根据提供商名称和工具名称获取工具"""
        provider = self.get_provider(provider_name)
        if provider:
            return provider.get_tool(tool_name)
        return None

    def _get_provider_tool_map(self):
        """获取工具提供商映射"""
        # 检测provider_tool_map是否为空
        if self.provider_map:
            return

        # 获取当前类/文件所在的文件夹路径
        current_path = os.path.abspath(__file__)
        providers_path = os.path.dirname(current_path)
        providers_yaml_path = os.path.join(providers_path, "providers.yaml")

        # 读取providers.yaml文件
        with open(providers_yaml_path, encoding="utf-8") as f:
            providers_yaml_data = yaml.safe_load(f)

        # 循环遍历providers.yaml文件中的数据，将数据存储到provider_map中
        for idx, provider_data in enumerate(providers_yaml_data):
            provider_entity = ProviderEntity(**provider_data)
            self.provider_map[provider_entity.name] = Provider(
                name=provider_entity.name,
                position=idx + 1,
                provider_entity=provider_entity,
            )
