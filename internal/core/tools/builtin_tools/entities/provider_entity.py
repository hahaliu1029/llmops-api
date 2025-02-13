import os
import yaml
from typing import Any
from pydantic import BaseModel, Field

from internal.core.tools.builtin_tools.entities.tool_entity import ToolEntity
from internal.lib.helper import dynamic_import


class ProviderEntity(BaseModel):
    """服务提供商实体，映射数据为provider.yaml里的每条记录"""

    name: str  # 名字
    label: str  # 标签，展示给前端
    description: str  # 描述
    icon: str  # 图标
    background: str  # 背景
    category: str  # 类别
    created_at: int = 0  # 创建时间


class Provider(BaseModel):
    """服务提供商，在该类下，可以获取到该服务提供商的所有工具，描述，图标等信息"""

    name: str  # 名字
    position: int  # 服务提供商的顺序
    provider_entity: ProviderEntity  # 服务提供商实体
    tool_entity_map: dict[str, ToolEntity] = Field(
        default_factory=dict
    )  # 服务提供商的工具映射
    tool_func_map: dict[str, Any] = Field(default_factory=dict)  # 服务提供商的工具映射

    def __init__(self, **kwargs):
        """构造函数，初始化服务提供商"""
        super().__init__(**kwargs)
        self._provider_init()

    def get_tool(self, tool_name: str) -> ToolEntity:
        """根据工具名字获取工具"""
        return self.tool_func_map.get(tool_name)

    def get_tool_entity(self, tool_name: str) -> ToolEntity:
        """根据工具名字获取工具实体"""
        return self.tool_entity_map.get(tool_name)

    def get_tool_entities(self) -> list[ToolEntity]:
        """获取所有工具实体"""
        return list(self.tool_entity_map.values())

    def _provider_init(self):
        """初始化服务提供商"""
        # 获取当前类的路径，计算得到对应服务提供商的地址/路径
        current_path = os.path.abspath(__file__)
        entities_path = os.path.dirname(current_path)
        provider_path = os.path.join(
            os.path.dirname(entities_path), "providers", self.name
        )
        print(provider_path)

        # 组装获取positions.yaml数据
        positions_yaml_path = os.path.join(provider_path, "positions.yaml")
        with open(positions_yaml_path, encoding="utf-8") as f:
            positions_yaml_data = yaml.safe_load(f)

        # 循环读取位置信息获取服务提供商的工具名字
        for tool_name in positions_yaml_data:
            # 获取工具的yaml数据
            tool_yaml_path = os.path.join(provider_path, f"{tool_name}.yaml")
            with open(tool_yaml_path, encoding="utf-8") as f:
                tool_yaml_data = yaml.safe_load(f)
            # 将工具的yaml数据转换为ToolEntity实体
            self.tool_entity_map[tool_name] = ToolEntity(**tool_yaml_data)

            # 动态导入对应的工具并存储到tool_func_map中
            self.tool_func_map[tool_name] = dynamic_import(
                f"internal.core.tools.builtin_tools.providers.{self.name}", tool_name
            )
